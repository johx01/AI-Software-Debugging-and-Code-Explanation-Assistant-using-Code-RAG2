"""Database setup and ORM models for JohnBot."""
import os
import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


# Use Neon PostgreSQL when DATABASE_URL is available.
# Fall back to local SQLite for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/johnbot.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://", 1)[0]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("postgresql"):
    # Neon PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
else:
    # Local SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def now():
    return datetime.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    files = relationship(
        "FileRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    github_connection = relationship(
        "GithubConnection",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    repo_ingest_jobs = relationship(
        "RepoIngestJob",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    status = Column(String, default="uploading")
    chunk_count = Column(Integer, default=0)
    content_hash = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    source = Column(String, default="upload")
    repo_ingest_job_id = Column(
        Integer,
        ForeignKey("repo_ingest_jobs.id"),
        nullable=True,
    )
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=True,
    )

    user = relationship("User", back_populates="files")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    theme = Column(String, default="system")
    enter_to_send = Column(Integer, default=1)
    show_sources = Column(Integer, default=1)

    user = relationship("User", back_populates="settings")


class GithubConnection(Base):
    __tablename__ = "github_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    github_user_id = Column(String, nullable=False)
    github_login = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    connected_at = Column(DateTime, default=now)

    user = relationship("User", back_populates="github_connection")


class RepoIngestJob(Base):
    __tablename__ = "repo_ingest_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_full_name = Column(String, nullable=False)
    status = Column(String, default="pending")
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=True,
    )

    user = relationship("User", back_populates="repo_ingest_jobs")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()