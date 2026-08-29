"""Orchestrates the end-to-end RAG flow for a single chat turn."""
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import FileRecord, Message
from app.services import llm_service
from app.services.retrieval_service import retrieve_relevant_chunks


def get_user_ready_file_ids(db: Session, user_id: int) -> set:
    rows = (
        db.query(FileRecord.id)
        .filter(FileRecord.user_id == user_id, FileRecord.status == "ready")
        .all()
    )
    return {r[0] for r in rows}


def get_recent_history(db: Session, conversation_id: int) -> list[dict]:
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(settings.MAX_HISTORY_MESSAGES)
        .all()
    )
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]


def answer_question(db: Session, user_id: int, conversation_id: int, question: str) -> Tuple[str, List[dict]]:
    """
    Runs the real RAG pipeline:
    question -> embed -> vector search -> retrieved chunks -> context -> one LLM call -> answer
    Returns (answer_text, sources) where sources only reflect actually retrieved chunks.
    """
    user_file_ids = get_user_ready_file_ids(db, user_id)
    chunks = retrieve_relevant_chunks(question, user_file_ids, top_k=settings.TOP_K)
    history = get_recent_history(db, conversation_id)

    answer = llm_service.generate_answer(question, chunks, history)

    sources = [
        {"file_name": c.file_name, "start_line": c.start_line, "end_line": c.end_line}
        for c in chunks
    ]
    return answer, sources


def make_title_from_question(question: str) -> str:
    """Generates a conversation title locally (no LLM call) from the first question."""
    cleaned = question.strip().rstrip("?.! ")
    words = cleaned.split()
    title = " ".join(words[:6])
    title = title[0].upper() + title[1:] if title else "New Chat"
    return title if len(title) <= 60 else title[:57] + "..."
