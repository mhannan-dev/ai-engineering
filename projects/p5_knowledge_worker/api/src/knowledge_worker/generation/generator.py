"""Faithful answer generator with citation validation and SSE streaming support."""

import json
from collections.abc import Iterator, Sequence

from knowledge_worker.config import Settings
from knowledge_worker.core.exceptions import LLMUnavailableError
from knowledge_worker.generation.llm import LLMClient
from knowledge_worker.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from knowledge_worker.generation.rewriter import QueryRewriter
from knowledge_worker.generation.validator import CitationValidator
from knowledge_worker.retrieval.models import RerankedChunk
from knowledge_worker.retrieval.retriever import HybridRetriever
from knowledge_worker.schemas.generation import (
    ChatRequest,
    ChatResponse,
    CitationValidationResult,
    StructuredAnswer,
)
from knowledge_worker.schemas.search import SearchResultChunk


class FaithfulGenerator:
    """Orchestrates hybrid retrieval, reranking, LLM answer synthesis, and citation validation."""

    def __init__(
        self,
        retriever: HybridRetriever,
        llm_client: LLMClient,
        settings: Settings,
        validator: CitationValidator | None = None,
        rewriter: QueryRewriter | None = None,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.settings = settings
        self.validator = validator or CitationValidator()
        self.rewriter = rewriter or QueryRewriter(llm_client)

    def _search_query(self, request: ChatRequest, history: Sequence[tuple[str, str]]) -> str:
        """The question retrieval and generation work with: the user's message, made
        standalone from the recent turns when it is a follow-up. Answers cite only this
        turn's passages; history only resolves what the question refers to."""
        return self.rewriter.rewrite(history, request.query)

    def _to_search_chunks(self, chunks: Sequence[RerankedChunk]) -> list[SearchResultChunk]:
        return [
            SearchResultChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_filename=c.document_filename,
                page=c.page,
                heading=c.heading,
                text=c.text,
                score=c.score,
                fused_rank=c.fused_rank,
                rerank_rank=c.rerank_rank,
            )
            for c in chunks
        ]

    def _get_abstention_text(self, was_banglish: bool, query: str) -> str:
        # If query contains Bengali characters or was detected as Banglish
        is_bn = was_banglish or any("\u0980" <= ch <= "\u09ff" for ch in query)
        if is_bn:
            return "প্রদত্ত নথিপত্রে এই প্রশ্নের উত্তর দেওয়ার জন্য পর্যাপ্ত তথ্য পাওয়া যায়নি।"
        return "The provided documents do not contain sufficient information to answer this question."

    def generate(
        self, user_id: str, request: ChatRequest, history: Sequence[tuple[str, str]] = ()
    ) -> ChatResponse:
        """Execute complete faithful RAG generation flow (synchronous).

        `history` is the conversation's recent (question, answer) turns, oldest first.
        """
        search_query = self._search_query(request, history)
        threshold = (
            request.threshold
            if request.threshold is not None
            else self.settings.RERANKER_THRESHOLD
        )
        candidate_limit = max(request.top_k * 4, self.settings.RERANKER_CANDIDATE_LIMIT)

        # 1. Retrieve & Rerank
        rerank_result = self.retriever.retrieve_and_rerank(
            user_id=user_id,
            query=search_query,
            limit=request.top_k,
            candidate_limit=candidate_limit,
            threshold=threshold,
        )

        top_chunks = rerank_result.chunks[: request.top_k]
        sources = self._to_search_chunks(top_chunks)

        # 2. Check Abstention Gate
        if rerank_result.is_abstention or not top_chunks:
            abstention_answer = self._get_abstention_text(
                rerank_result.was_banglish, request.query
            )
            reason = (
                f"Top relevance score below threshold {threshold:.2f}."
                if top_chunks
                else "No matching documents found in the database."
            )
            return ChatResponse(
                query=request.query,
                normalized_query=rerank_result.normalized_query,
                was_banglish=rerank_result.was_banglish,
                answer=abstention_answer,
                citations=[],
                is_abstention=True,
                abstention_reason=reason,
                validation=CitationValidationResult(is_valid=True),
                sources=sources,
            )

        # 3. Build Grounded Prompt
        user_prompt = build_user_prompt(
            query=search_query,
            chunks=top_chunks,
            normalized_query=rerank_result.normalized_query,
            was_banglish=rerank_result.was_banglish,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        temperature = (
            request.temperature
            if request.temperature is not None
            else self.settings.LLM_TEMPERATURE
        )

        # 4. LLM Generation. Provider errors carry keys, model names and paths, so they are
        # chained onto a generic error: the endpoint logs the cause and returns only the message.
        try:
            structured: StructuredAnswer = self.llm_client.generate_structured(
                messages=messages,
                response_model=StructuredAnswer,
                temperature=temperature,
                max_tokens=self.settings.LLM_MAX_TOKENS,
            )
        except Exception as exc:
            raise LLMUnavailableError() from exc

        # 5. Citation Validation
        validation = self.validator.validate(
            answer=structured.answer,
            retrieved_chunks=top_chunks,
            structured_citations=structured.citations,
        )

        # If LLM explicitly chose to abstain
        is_abstention = structured.is_abstention
        abstention_reason = structured.abstention_reason

        return ChatResponse(
            query=request.query,
            normalized_query=rerank_result.normalized_query,
            was_banglish=rerank_result.was_banglish,
            answer=structured.answer,
            citations=validation.valid_citations or structured.citations,
            is_abstention=is_abstention,
            abstention_reason=abstention_reason,
            validation=validation,
            sources=sources,
        )

    def stream_events(
        self, user_id: str, request: ChatRequest, history: Sequence[tuple[str, str]] = ()
    ) -> Iterator[dict]:
        """Yield structured SSE events for real-time token streaming and citation verification.

        `history` is the conversation's recent (question, answer) turns, oldest first.
        """
        threshold = (
            request.threshold
            if request.threshold is not None
            else self.settings.RERANKER_THRESHOLD
        )
        candidate_limit = max(request.top_k * 4, self.settings.RERANKER_CANDIDATE_LIMIT)

        # Event: retrieving status
        yield {"event": "status", "data": {"stage": "retrieving", "message": "Searching & reranking..."}}

        # After the first event, so the client shows progress while a follow-up is rewritten.
        search_query = self._search_query(request, history)
        rerank_result = self.retriever.retrieve_and_rerank(
            user_id=user_id,
            query=search_query,
            limit=request.top_k,
            candidate_limit=candidate_limit,
            threshold=threshold,
        )

        top_chunks = rerank_result.chunks[: request.top_k]
        sources = self._to_search_chunks(top_chunks)

        # Event: retrieved sources
        yield {
            "event": "sources",
            "data": {
                "query": request.query,
                "normalized_query": rerank_result.normalized_query,
                "was_banglish": rerank_result.was_banglish,
                "sources": [s.model_dump() for s in sources],
            },
        }

        # Check Abstention
        if rerank_result.is_abstention or not top_chunks:
            abstention_msg = self._get_abstention_text(rerank_result.was_banglish, request.query)
            reason = (
                f"Top relevance score below threshold {threshold:.2f}."
                if top_chunks
                else "No matching documents found in the database."
            )
            yield {
                "event": "abstention",
                "data": {"reason": reason, "answer": abstention_msg},
            }
            yield {
                "event": "done",
                "data": {
                    "answer": abstention_msg,
                    "citations": [],
                    "is_abstention": True,
                    "abstention_reason": reason,
                    "validation": {"is_valid": True, "warnings": []},
                },
            }
            return

        # Stream Generation
        yield {"event": "status", "data": {"stage": "generating", "message": "Synthesizing answer..."}}

        user_prompt = build_user_prompt(
            query=search_query,
            chunks=top_chunks,
            normalized_query=rerank_result.normalized_query,
            was_banglish=rerank_result.was_banglish,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        temperature = (
            request.temperature
            if request.temperature is not None
            else self.settings.LLM_TEMPERATURE
        )

        full_answer_parts: list[str] = []
        tokens = self.llm_client.stream_text(
            messages=messages,
            temperature=temperature,
            max_tokens=self.settings.LLM_MAX_TOKENS,
        )
        # The provider can fail on the first token or halfway through the answer.
        try:
            for token in tokens:
                full_answer_parts.append(token)
                yield {"event": "token", "data": {"token": token}}
        except Exception as exc:
            raise LLMUnavailableError() from exc

        full_answer = "".join(full_answer_parts)

        # Event: validating citations
        yield {"event": "status", "data": {"stage": "validating", "message": "Validating citations..."}}

        validation = self.validator.validate(
            answer=full_answer,
            retrieved_chunks=top_chunks,
        )

        yield {"event": "validation", "data": validation.model_dump()}

        # Event: done
        yield {
            "event": "done",
            "data": {
                "query": request.query,
                "answer": full_answer,
                "citations": [c.model_dump() for c in validation.valid_citations],
                "is_abstention": False,
                "validation": validation.model_dump(),
                "sources": [s.model_dump() for s in sources],
            },
        }

    def format_sse(self, event_dict: dict) -> str:
        """Format an event dictionary into a Server-Sent Events (SSE) string."""
        event_name = event_dict.get("event", "message")
        data_str = json.dumps(event_dict.get("data", {}), ensure_ascii=False)
        return f"event: {event_name}\ndata: {data_str}\n\n"
