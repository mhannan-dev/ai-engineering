"""Schemas for faithful generation, citations, validation, and chat endpoints."""

from pydantic import BaseModel, Field

from knowledge_worker.schemas.search import SearchResultChunk


class Citation(BaseModel):
    """A citation pointing to a specific source document and section/page."""

    document_filename: str = Field(..., description="Indexed filename, e.g. handbook.md or policy.pdf")
    page: int | None = Field(default=None, description="1-indexed page number if applicable")
    heading: str | None = Field(default=None, description="Section heading if applicable")
    chunk_id: str | None = Field(default=None, description="Internal chunk identifier if known")
    quoted_text: str | None = Field(default=None, description="Supporting excerpt from the chunk")


class CitationValidationResult(BaseModel):
    """Result of validating citations against actual retrieved source chunks."""

    is_valid: bool = Field(..., description="True if all citations are grounded in retrieved chunks")
    valid_citations: list[Citation] = Field(default_factory=list)
    hallucinated_citations: list[Citation] = Field(
        default_factory=list, description="Citations to files not present in retrieved context"
    )
    unmatched_pages: list[Citation] = Field(
        default_factory=list, description="Citations with pages that don't match retrieved chunk pages"
    )
    warnings: list[str] = Field(default_factory=list)


class StructuredAnswer(BaseModel):
    """Structured response model used with Instructor/LiteLLM."""

    answer: str = Field(
        ...,
        description=(
            "Faithful answer with inline bracketed citations, "
            "e.g. [filename.pdf, Page 2] or [filename.md, Section]"
        ),
    )
    citations: list[Citation] = Field(
        default_factory=list, description="List of all citations supporting the answer"
    )
    is_abstention: bool = Field(
        default=False,
        description="True if the provided documents do not contain enough information to answer",
    )
    abstention_reason: str | None = Field(
        default=None, description="Explanation of why the assistant abstained"
    )


class ChatRequest(BaseModel):
    """User request for faithful RAG answer generation."""

    query: str = Field(
        ..., min_length=1, max_length=1000, description="Question in English, Bangla, or Banglish"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of reranked passages to supply as context")
    threshold: float | None = Field(default=None, description="Custom abstention threshold override")
    temperature: float | None = Field(default=None, description="LLM sampling temperature")


class ChatResponse(BaseModel):
    """Complete response containing faithful answer, citations, validation, and sources."""

    query: str
    normalized_query: str
    was_banglish: bool
    answer: str
    citations: list[Citation]
    is_abstention: bool
    abstention_reason: str | None = None
    validation: CitationValidationResult
    sources: list[SearchResultChunk] = Field(default_factory=list)
