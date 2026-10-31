"""Saved chat conversations, scoped to their owner."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from knowledge_worker.core.exceptions import NotFoundError
from knowledge_worker.db.models import ConversationModel, MessageModel

TITLE_MAX = 80


def make_title(question: str) -> str:
    """The first question, on one line and cut at a word boundary. No LLM call needed."""
    text = " ".join(question.split())
    if len(text) <= TITLE_MAX:
        return text
    cut = text[:TITLE_MAX].rsplit(" ", 1)[0] or text[:TITLE_MAX]
    return cut + "…"


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def list_conversations(
        self, user_id: str, limit: int, offset: int
    ) -> tuple[list[ConversationModel], int]:
        base = select(ConversationModel).where(ConversationModel.user_id == user_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = self.db.scalars(
            base.order_by(ConversationModel.updated_at.desc(), ConversationModel.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def get(self, user_id: str, conversation_id: str, with_messages: bool = False) -> ConversationModel:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id, ConversationModel.user_id == user_id
        )
        if with_messages:
            stmt = stmt.options(selectinload(ConversationModel.messages))
        conversation = self.db.scalar(stmt)
        # Someone else's conversation looks exactly like a missing one.
        if conversation is None:
            raise NotFoundError("Conversation not found.")
        return conversation

    def recent_turns(self, user_id: str, conversation_id: str, turns: int) -> list[tuple[str, str]]:
        """The last `turns` (question, answer) pairs, oldest first, for rewriting follow-ups.
        Raises NotFoundError if the conversation isn't this user's."""
        conversation = self.get(user_id, conversation_id)
        if turns <= 0:
            return []
        recent = self.db.scalars(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation.id)
            .order_by(MessageModel.created_at.desc())
            .limit(turns * 2)
        ).all()
        ordered = list(reversed(recent))
        return [
            (asked.content, answered.content)
            for asked, answered in zip(ordered, ordered[1:], strict=False)
            if asked.role == "user" and answered.role == "assistant"
        ]

    def delete(self, user_id: str, conversation_id: str) -> None:
        self.db.delete(self.get(user_id, conversation_id))
        self.db.commit()

    def save_turn(
        self,
        user_id: str,
        conversation_id: str | None,
        question: str,
        answer: str,
        *,
        citations: list[dict[str, Any]] | None = None,
        sources: list[dict[str, Any]] | None = None,
        validation: dict[str, Any] | None = None,
        is_abstention: bool = False,
    ) -> ConversationModel:
        """Store one question and its answer, creating the conversation when the id is None.

        A turn is saved only once the answer is complete, so a failed or stopped answer never
        leaves a question without its reply in the history.
        """
        now = datetime.now(UTC)
        if conversation_id is None:
            conversation = ConversationModel(
                id=str(uuid.uuid4()), user_id=user_id, title=make_title(question), created_at=now
            )
            self.db.add(conversation)
        else:
            conversation = self.get(user_id, conversation_id)
        conversation.updated_at = now

        # The answer is stamped 1 µs after the question: two now() calls can return the same
        # value on Windows, which would make their order arbitrary.
        self.db.add_all([
            MessageModel(
                id=str(uuid.uuid4()), conversation_id=conversation.id, role="user",
                content=question, created_at=now,
            ),
            MessageModel(
                id=str(uuid.uuid4()), conversation_id=conversation.id, role="assistant",
                content=answer, citations=citations, sources=sources, validation=validation,
                is_abstention=is_abstention, created_at=now + timedelta(microseconds=1),
            ),
        ])
        self.db.commit()
        return conversation
