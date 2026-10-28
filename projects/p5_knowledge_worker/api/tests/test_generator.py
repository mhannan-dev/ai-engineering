"""Unit tests for FaithfulGenerator."""

from unittest.mock import MagicMock

from knowledge_worker.config import Settings
from knowledge_worker.generation.generator import FaithfulGenerator
from knowledge_worker.generation.llm import FakeLLMClient
from knowledge_worker.retrieval.models import RerankedChunk, RerankResult
from knowledge_worker.schemas.generation import ChatRequest, Citation, StructuredAnswer


def _make_mock_retriever(chunks, is_abstention=False, was_banglish=False, normalized=""):
    retriever = MagicMock()
    retriever.retrieve_and_rerank.return_value = RerankResult(
        query="test query",
        normalized_query=normalized or "test query",
        was_banglish=was_banglish,
        is_abstention=is_abstention,
        threshold=0.25,
        chunks=chunks,
    )
    return retriever


def test_generator_abstains_when_retriever_abstains():
    settings = Settings()
    retriever = _make_mock_retriever([], is_abstention=True)
    llm = FakeLLMClient()
    generator = FaithfulGenerator(retriever, llm, settings)

    req = ChatRequest(query="What is the quantum flux coefficient?")
    resp = generator.generate(user_id="local", request=req)

    assert resp.is_abstention is True
    assert "not contain sufficient information" in resp.answer
    assert resp.citations == []
    assert resp.validation.is_valid is True


def test_generator_bangla_abstention_text():
    settings = Settings()
    retriever = _make_mock_retriever([], is_abstention=True, was_banglish=True, normalized="ছুটি")
    llm = FakeLLMClient()
    generator = FaithfulGenerator(retriever, llm, settings)

    req = ChatRequest(query="kobe chuti pabo?")
    resp = generator.generate(user_id="local", request=req)

    assert resp.is_abstention is True
    # Should reply in Bengali script explaining information is not found
    assert "তথ্য পাওয়া যায়নি" in resp.answer
    assert resp.was_banglish is True


def test_generator_successful_answer_with_citations():
    settings = Settings()
    chunk = RerankedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        document_filename="handbook.pdf",
        page=4,
        heading="Vacations",
        text="All regular employees receive 20 days of annual leave.",
        score=0.92,
        fused_rank=1,
        rerank_rank=1,
    )
    retriever = _make_mock_retriever([chunk], is_abstention=False)

    fake_answer = StructuredAnswer(
        answer="Employees are entitled to 20 days of annual leave [handbook.pdf, Page 4].",
        citations=[Citation(document_filename="handbook.pdf", page=4)],
        is_abstention=False,
    )
    llm = FakeLLMClient(canned_response=fake_answer)
    generator = FaithfulGenerator(retriever, llm, settings)

    req = ChatRequest(query="How much leave do I get?")
    resp = generator.generate(user_id="local", request=req)

    assert resp.is_abstention is False
    assert "20 days of annual leave" in resp.answer
    assert len(resp.citations) == 1
    assert resp.citations[0].document_filename == "handbook.pdf"
    assert resp.citations[0].page == 4
    assert resp.validation.is_valid is True
    assert len(resp.sources) == 1
    assert resp.sources[0].chunk_id == "chunk-1"


def test_generator_stream_events_flow():
    settings = Settings()
    chunk = RerankedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        document_filename="handbook.pdf",
        page=1,
        heading="Intro",
        text="Office hours are from 9 AM to 5 PM.",
        score=0.88,
        fused_rank=1,
        rerank_rank=1,
    )
    retriever = _make_mock_retriever([chunk], is_abstention=False)

    fake_answer = StructuredAnswer(
        answer="Office hours run from 9 AM to 5 PM [handbook.pdf, Page 1].",
        citations=[Citation(document_filename="handbook.pdf", page=1)],
        is_abstention=False,
    )
    llm = FakeLLMClient(canned_response=fake_answer)
    generator = FaithfulGenerator(retriever, llm, settings)

    req = ChatRequest(query="What are the office hours?")
    events = list(generator.stream_events(user_id="local", request=req))

    event_types = [e["event"] for e in events]
    assert "status" in event_types
    assert "sources" in event_types
    assert "token" in event_types
    assert "validation" in event_types
    assert "done" in event_types

    # Test SSE formatting helper
    sse_text = generator.format_sse(events[0])
    assert sse_text.startswith("event: status\ndata: ")
    assert sse_text.endswith("\n\n")
