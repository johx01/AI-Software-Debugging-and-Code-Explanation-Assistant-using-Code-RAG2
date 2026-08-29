"""Pydantic schemas for request/response validation."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Files ----------
class FileOut(BaseModel):
    id: int
    file_name: str
    language: Optional[str]
    status: str
    chunk_count: int
    created_at: str

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str


class SourceRef(BaseModel):
    file_name: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    sources: List[SourceRef] = []


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []


# ---------- Settings ----------
class SettingsOut(BaseModel):
    theme: str
    enter_to_send: bool
    show_sources: bool
    provider: str
    model: str


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    enter_to_send: Optional[bool] = None
    show_sources: Optional[bool] = None
