"""Handles file validation, storage, and triggers RAG ingestion."""
import hashlib
import logging
import os

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings, SUPPORTED_EXTENSIONS
from app.database.database import FileRecord
from app.rag import loader, chunker, embedder
from app.rag.vector_store import get_vector_store

logger = logging.getLogger("johnbot")


def validate_file(file: UploadFile, content: bytes):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext or 'unknown'}")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")


def save_and_ingest(db: Session, user_id: int, file: UploadFile, content: bytes) -> FileRecord:
    validate_file(file, content)

    content_hash = hashlib.sha256(content).hexdigest()

    # Avoid re-indexing an unchanged file already uploaded by this user.
    existing = (
        db.query(FileRecord)
        .filter(FileRecord.user_id == user_id, FileRecord.content_hash == content_hash)
        .first()
    )
    if existing and existing.status == "ready":
        return existing

    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    record = FileRecord(
        user_id=user_id,
        file_name=file.filename,
        file_path=file_path,
        status="processing",
        content_hash=content_hash,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        _process_file(record)
        record.status = "ready"
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process file %s", file.filename)
        record.status = "error"
        record.error_message = str(exc)
    db.commit()
    db.refresh(record)
    return record


def _process_file(record: FileRecord):
    text = loader.read_file_text(record.file_path)
    language = loader.detect_language(record.file_name)
    record.language = language

    chunks = chunker.chunk_code(text, language)
    logger.info("File %s -> %d chunks", record.file_name, len(chunks))
    if not chunks:
        record.chunk_count = 0
        return

    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_texts(texts)

    store = get_vector_store()
    store.add_chunks(record.id, record.file_name, chunks, embeddings)
    record.chunk_count = len(chunks)
    logger.info("Embeddings generated and indexed for %s", record.file_name)


def delete_file(db: Session, record: FileRecord):
    get_vector_store().delete_file(record.id)
    if os.path.exists(record.file_path):
        os.remove(record.file_path)
    db.delete(record)
    db.commit()
