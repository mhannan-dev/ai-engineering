"""Rewrite a follow-up message into a standalone question before retrieval.

"And sick leave?" means nothing to a search engine on its own. With the recent turns, an LLM
can turn it into "How many days of sick leave do employees get?", which retrieval and the
answer generator can both work with. The first message of a conversation needs no rewrite, so
it costs no LLM call.
"""

import logging
from collections.abc import Sequence

from pydantic import BaseModel, Field

from knowledge_worker.generation.llm import LLMClient
from knowledge_worker.generation.prompts import REWRITE_SYSTEM_PROMPT, build_rewrite_prompt

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 1000  # same limit as ChatRequest.query


class StandaloneQuestion(BaseModel):
    question: str = Field(description="The latest message rewritten as a standalone question")


class QueryRewriter:
    def __init__(self, llm_client: LLMClient, max_answer_chars: int = 600):
        self._llm = llm_client
        self._max_answer_chars = max_answer_chars

    def rewrite(self, history: Sequence[tuple[str, str]], question: str) -> str:
        """Return a standalone version of `question`, given (question, answer) turns, oldest
        first. Falls back to `question` itself when there is no history or the rewrite fails:
        searching with the raw follow-up is worse, but better than no answer."""
        if not history:
            return question
        messages = [
            {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
            {"role": "user", "content": build_rewrite_prompt(history, question, self._max_answer_chars)},
        ]
        try:
            result = self._llm.generate_structured(
                messages=messages, response_model=StandaloneQuestion, temperature=0.0, max_tokens=200
            )
        except Exception:
            logger.warning("Query rewrite failed; searching with the original question", exc_info=True)
            return question
        rewritten = " ".join(result.question.split())
        if not rewritten or len(rewritten) > MAX_QUESTION_CHARS:
            return question
        return rewritten
