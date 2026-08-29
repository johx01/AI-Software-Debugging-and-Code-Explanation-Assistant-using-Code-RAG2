import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db, User, Conversation, Message
from app.models.schemas import ChatRequest, ChatResponse, SourceRef, ConversationOut, ConversationDetail, MessageOut
from app.services.rag_service import answer_question, make_title_from_question
from app.utils.auth_utils import get_current_user

logger = logging.getLogger("johnbot")
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conversation = None
    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation is None:
        conversation = Conversation(user_id=current_user.id, title=make_title_from_question(question))
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(Message(conversation_id=conversation.id, role="user", content=question))
    db.commit()

    try:
        answer, sources = answer_question(db, current_user.id, conversation.id, question)
    except RuntimeError as exc:
        logger.error("RAG pipeline failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    db.add(Message(
        conversation_id=conversation.id, role="assistant", content=answer,
        sources=json.dumps(sources),
    ))
    conversation.updated_at = conversation.updated_at  # trigger onupdate
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=answer,
        sources=[SourceRef(**s) for s in sources],
    )


@router.get("/chats", response_model=List[ConversationOut])
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        ConversationOut(
            id=r.id, title=r.title,
            created_at=r.created_at.isoformat(), updated_at=r.updated_at.isoformat(),
        ) for r in rows
    ]


@router.get("/chats/{chat_id}", response_model=ConversationDetail)
def get_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == chat_id, Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(Message).filter(Message.conversation_id == chat_id).order_by(Message.id.asc()).all()
    return ConversationDetail(
        id=conversation.id, title=conversation.title,
        created_at=conversation.created_at.isoformat(), updated_at=conversation.updated_at.isoformat(),
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content, sources=m.sources, created_at=m.created_at.isoformat())
            for m in messages
        ],
    )


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == chat_id, Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}
