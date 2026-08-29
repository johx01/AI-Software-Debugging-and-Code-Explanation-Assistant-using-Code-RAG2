"""
A small local vector store backed by a single pickle file on disk.

Stores, per chunk: embedding vector, chunk text, file_id, file_name,
start_line, end_line. Supports similarity search and deletion by file_id.
No external vector database service is required, keeping local setup simple.
"""
import os
import pickle
import threading
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from app.config import settings


@dataclass
class ChunkRecord:
    chunk_id: str
    file_id: int
    file_name: str
    text: str
    start_line: int
    end_line: int
    embedding: np.ndarray


class VectorStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self.records: List[ChunkRecord] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "rb") as f:
                self.records = pickle.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "wb") as f:
            pickle.dump(self.records, f)

    def add_chunks(self, file_id: int, file_name: str, chunks: List[dict], embeddings: np.ndarray):
        with self._lock:
            for i, chunk in enumerate(chunks):
                record = ChunkRecord(
                    chunk_id=f"{file_id}-{i}",
                    file_id=file_id,
                    file_name=file_name,
                    text=chunk["text"],
                    start_line=chunk["start_line"],
                    end_line=chunk["end_line"],
                    embedding=embeddings[i],
                )
                self.records.append(record)
            self._save()

    def delete_file(self, file_id: int):
        with self._lock:
            self.records = [r for r in self.records if r.file_id != file_id]
            self._save()

    def search(self, query_embedding: np.ndarray, user_file_ids: set, top_k: int = None) -> List[ChunkRecord]:
        """Return the top_k most similar chunks, restricted to the given file ids."""
        top_k = top_k or settings.TOP_K
        candidates = [r for r in self.records if r.file_id in user_file_ids]
        if not candidates:
            return []
        matrix = np.stack([r.embedding for r in candidates])
        # embeddings are already L2-normalized, so dot product == cosine similarity
        scores = matrix @ query_embedding
        top_indices = np.argsort(-scores)[:top_k]
        return [candidates[i] for i in top_indices if scores[i] > 0]


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(settings.VECTOR_STORE_PATH)
    return _store
