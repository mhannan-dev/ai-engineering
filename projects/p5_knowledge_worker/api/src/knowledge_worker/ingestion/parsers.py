"""Turn an uploaded file into sections of text that remember where they came from.

A section is the unit a citation can point at: a PDF page, or the text under one heading in
DOCX / Markdown / HTML. Chunks never cross a section boundary.
"""

import io
import re
from dataclasses import dataclass
from typing import Literal

import pymupdf
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from docx.table import Table as DocxTable
from docx.table import _Row as DocxRow

from knowledge_worker.text.normalize import normalize_text

DocumentFormat = Literal["pdf", "docx", "md", "html", "txt"]


@dataclass(frozen=True)
class Section:
    text: str
    page: int | None = None  # 1-based, PDFs only
    heading: str | None = None


class ParseError(Exception):
    """The file is valid but its text cannot be used (scanned, legacy encoding, empty)."""


def parse_document(data: bytes, fmt: DocumentFormat) -> list[Section]:
    parser = {"pdf": _parse_pdf, "docx": _parse_docx, "md": _parse_markdown, "html": _parse_html,
              "txt": _parse_txt}[fmt]
    try:
        sections = [s for s in parser(data) if s.text]
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"The file is damaged or is not a valid {fmt.upper()} file.") from exc
    if not sections:
        raise ParseError(
            "No text could be extracted. If this is a scanned PDF, it needs OCR first."
        )
    return sections


def _parse_pdf(data: bytes) -> list[Section]:
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        if pdf.needs_pass:
            raise ParseError("This PDF is password-protected. Remove the password and upload again.")
        return [
            Section(text=normalize_text(page.get_text("text", sort=True)), page=number)
            for number, page in enumerate(pdf, start=1)
        ]


def _parse_docx(data: bytes) -> list[Section]:
    doc = DocxDocument(io.BytesIO(data))
    sections: list[Section] = []
    heading: str | None = None
    lines: list[str] = []

    def flush() -> None:
        if lines:
            sections.append(Section(text=normalize_text("\n".join(lines)), heading=heading))
            lines.clear()

    # Walk paragraphs and tables in document order, so a table is labelled with the heading
    # it sits under (for citations and BM25) instead of being collected separately at the end.
    for block in doc.iter_inner_content():
        if isinstance(block, DocxTable):
            # Tables carry a lot of policy content (leave tables, fee schedules). Each table is
            # its own section so its rows never merge into the surrounding paragraphs.
            flush()
            rows = [row for row in (_docx_row_text(r) for r in block.rows) if row]
            if rows:
                sections.append(Section(text=normalize_text("\n".join(rows)), heading=heading))
            continue
        text = block.text.strip()
        if not text:
            continue
        style = (block.style.name or "") if block.style is not None else ""
        if style.startswith("Heading") or style == "Title":
            flush()
            heading = normalize_text(text)
        else:
            lines.append(text)
    flush()
    return sections


def _docx_row_text(row: DocxRow) -> str:
    """Cells joined by ' | '. A merged cell is returned once per column it spans, so repeats
    of the same underlying cell are skipped."""
    # Keep the elements themselves: lxml proxies are only identical while referenced, so ids
    # of discarded proxies could be reused.
    seen: list[object] = []
    cells: list[str] = []
    for cell in row.cells:
        if any(cell._tc is tc for tc in seen):
            continue
        seen.append(cell._tc)
        cells.append(cell.text.strip())
    return " | ".join(cells) if any(cells) else ""


_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def _parse_markdown(data: bytes) -> list[Section]:
    sections: list[Section] = []
    heading: str | None = None
    lines: list[str] = []
    for line in data.decode("utf-8-sig").splitlines():
        match = _MD_HEADING.match(line)
        if match:
            if lines:
                sections.append(Section(text=normalize_text("\n".join(lines)), heading=heading))
                lines = []
            heading = normalize_text(match.group(2))
        else:
            lines.append(line)
    if lines:
        sections.append(Section(text=normalize_text("\n".join(lines)), heading=heading))
    return sections


def _parse_html(data: bytes) -> list[Section]:
    soup = BeautifulSoup(data.decode("utf-8-sig", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        tag.decompose()

    sections: list[Section] = []
    heading: str | None = None
    lines: list[str] = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "pre"]):
        if el.find_parent(["p", "li", "td", "pre"]):
            continue  # already included in its parent's text
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name.startswith("h"):
            if lines:
                sections.append(Section(text=normalize_text("\n".join(lines)), heading=heading))
                lines = []
            heading = normalize_text(text)
        else:
            lines.append(text)
    if lines:
        sections.append(Section(text=normalize_text("\n".join(lines)), heading=heading))
    return sections


def _parse_txt(data: bytes) -> list[Section]:
    return [Section(text=normalize_text(data.decode("utf-8-sig")))]
