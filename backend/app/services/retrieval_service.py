"""Embeds a user question and retrieves the most relevant code chunks."""
from typing import List

from app.rag import embedder
from app.rag.vector_store import get_vector_store, ChunkRecord


def retrieve_relevant_chunks(question: str, user_file_ids: set, top_k: int = None) -> List[ChunkRecord]:
    if not user_file_ids:
        return []
    query_embedding = embedder.embed_query(question)
    store = get_vector_store()
    return store.search(query_embedding, user_file_ids, top_k=top_k)
