"""Citation extraction and grounding validator for faithful RAG answers."""

import re
from collections.abc import Sequence

from knowledge_worker.retrieval.models import RerankedChunk, RetrievedChunk
from knowledge_worker.schemas.generation import Citation, CitationValidationResult

# Matches bracketed citations like:
# [handbook.pdf, Page 3]
# [handbook.pdf, p. 3]
# [operations.md, 16. Citation requirements]
# [company_policy.docx]
_CITATION_PATTERN = re.compile(r"\[([^\]\n]+)\]")
_PAGE_PATTERN = re.compile(r"(?:[Pp]age|[Pp]\.?)\s*(\d+)")


class CitationValidator:
    """Validates that all citations in an LLM answer are grounded in retrieved chunks."""

    def extract_citations(self, text: str) -> list[Citation]:
        """Extract all bracketed citations from text."""
        citations: list[Citation] = []
        seen: set[tuple[str, int | None, str | None]] = set()

        for match in _CITATION_PATTERN.finditer(text):
            raw_content = match.group(1).strip()
            # If multiple citations are separated by semicolon: [doc1.pdf, Page 1; doc2.md]
            items = [item.strip() for item in raw_content.split(";") if item.strip()]

            for item in items:
                citation = self._parse_citation_item(item)
                if citation:
                    key = (
                        citation.document_filename.lower(),
                        citation.page,
                        citation.heading.lower() if citation.heading else None,
                    )
                    if key not in seen:
                        seen.add(key)
                        citations.append(citation)

        return citations

    def _parse_citation_item(self, item: str) -> Citation | None:
        """Parse a single citation string like 'handbook.pdf, Page 3' or 'handbook.md'."""
        if not item:
            return None

        # Check for comma separation
        if "," in item:
            parts = item.split(",", 1)
            filename = parts[0].strip()
            detail = parts[1].strip()

            page_match = _PAGE_PATTERN.search(detail)
            if page_match:
                page = int(page_match.group(1))
                return Citation(document_filename=filename, page=page)
            else:
                return Citation(document_filename=filename, heading=detail)

        # No comma: check if it's just a filename or has page pattern
        page_match = _PAGE_PATTERN.search(item)
        if page_match and "." not in item:
            # e.g. "Page 3"
            page = int(page_match.group(1))
            return Citation(document_filename="", page=page)

        return Citation(document_filename=item.strip())

    def validate(
        self,
        answer: str,
        retrieved_chunks: Sequence[RerankedChunk | RetrievedChunk],
        structured_citations: Sequence[Citation] | None = None,
    ) -> CitationValidationResult:
        """Validate answer citations against the actual retrieved context chunks.

        Checks:
        1. Document existence: The cited document must exist in retrieved_chunks.
        2. Page grounding: If a page is cited, the retrieved chunk must have that page.
        3. Heading grounding: If a heading is cited, check for matching chunk heading.
        4. Excerpt grounding: If quoted text is provided, verify it exists in chunk text.
        """
        # Gather all candidate citations to validate (both extracted from text and structured)
        extracted = self.extract_citations(answer)
        all_citations: list[Citation] = []
        seen: set[tuple[str, int | None, str | None]] = set()

        for c in list(structured_citations or []) + extracted:
            fn = c.document_filename.strip().lower()
            key = (fn, c.page, c.heading.strip().lower() if c.heading else None)
            if key not in seen and fn:
                seen.add(key)
                all_citations.append(c)

        if not all_citations:
            # If no citations were found in the answer
            return CitationValidationResult(
                is_valid=True,
                valid_citations=[],
                hallucinated_citations=[],
                unmatched_pages=[],
                warnings=["No citations found in the generated response."] if answer.strip() else [],
            )

        # Index retrieved chunks by normalized filename
        chunks_by_fn: dict[str, list[RerankedChunk | RetrievedChunk]] = {}
        for chunk in retrieved_chunks:
            fn_key = chunk.document_filename.strip().lower()
            chunks_by_fn.setdefault(fn_key, []).append(chunk)

        valid_citations: list[Citation] = []
        hallucinated_citations: list[Citation] = []
        unmatched_pages: list[Citation] = []
        warnings: list[str] = []

        for citation in all_citations:
            fn_key = citation.document_filename.strip().lower()
            matching_chunks = chunks_by_fn.get(fn_key)

            if not matching_chunks:
                # 1. Hallucinated document filename
                hallucinated_citations.append(citation)
                warnings.append(
                    f"Hallucinated source: Document '{citation.document_filename}' was not among "
                    "the retrieved context passages."
                )
                continue

            # 2. Check page grounding if page was specified
            page_error = False
            if citation.page is not None:
                has_page = any(c.page == citation.page for c in matching_chunks)
                if not has_page:
                    unmatched_pages.append(citation)
                    avail_pages = sorted({c.page for c in matching_chunks if c.page is not None})
                    warnings.append(
                        f"Page mismatch: Page {citation.page} was cited for "
                        f"'{citation.document_filename}', but retrieved pages were {avail_pages}."
                    )
                    page_error = True

            # 3. Check heading if specified
            if citation.heading and not page_error:
                heading_lower = citation.heading.strip().lower()
                has_heading = any(
                    c.heading and (
                        heading_lower in c.heading.lower() or c.heading.lower() in heading_lower
                    )
                    for c in matching_chunks
                )
                if not has_heading:
                    warnings.append(
                        f"Unmatched heading: Heading '{citation.heading}' was not found in "
                        f"retrieved chunks for '{citation.document_filename}'."
                    )

            # 4. Check quoted text if specified
            if citation.quoted_text and not page_error:
                quote_clean = " ".join(citation.quoted_text.lower().split())
                has_quote = any(
                    quote_clean in " ".join(c.text.lower().split()) for c in matching_chunks
                )
                if not has_quote:
                    warnings.append(
                        f"Unmatched quote: Supporting quote '{citation.quoted_text[:40]}...' "
                        f"was not found in retrieved chunks for '{citation.document_filename}'."
                    )

            if not page_error:
                # Associate chunk_id if available
                chunk_id = None
                for c in matching_chunks:
                    if citation.page is not None and c.page == citation.page:
                        chunk_id = c.chunk_id
                        break
                    elif citation.heading and c.heading and citation.heading.lower() in c.heading.lower():
                        chunk_id = c.chunk_id
                        break
                if not chunk_id and matching_chunks:
                    chunk_id = matching_chunks[0].chunk_id

                valid_citation = Citation(
                    document_filename=citation.document_filename,
                    page=citation.page,
                    heading=citation.heading,
                    chunk_id=chunk_id,
                    quoted_text=citation.quoted_text,
                )
                valid_citations.append(valid_citation)

        is_valid = len(hallucinated_citations) == 0 and len(unmatched_pages) == 0

        return CitationValidationResult(
            is_valid=is_valid,
            valid_citations=valid_citations,
            hallucinated_citations=hallucinated_citations,
            unmatched_pages=unmatched_pages,
            warnings=warnings,
        )
