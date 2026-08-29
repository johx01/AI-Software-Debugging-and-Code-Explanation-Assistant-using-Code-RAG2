"""
Jina AI embedding service.

This module is responsible only for converting code/query text
into embedding vectors for the RAG vector store. It uses the
Jina AI Embeddings API (https://jina.ai/embeddings) over plain HTTP.
Chat responses are handled separately by llm_service.py via Gemini.
"""

import logging
import time

import numpy as np
import requests

from app.config import settings

logger = logging.getLogger("johnbot")

_JINA_ENDPOINT = "https://api.jina.ai/v1/embeddings"

# jina-embeddings-v3 is Matryoshka-trained and supports truncating its
# native 1024-dim output via the "dimensions" request field. 768 matches
# the vector store's previous dimension and keeps requests small.
EMBEDDING_DIM = 768

_BATCH_SIZE = 20
_MAX_RETRIES = 5
_BASE_BACKOFF_SECONDS = 5


def _embed_batch(texts: list[str], task_type: str) -> np.ndarray:
    """Embed a single batch of texts, retrying on rate limits."""

    if not settings.JINA_API_KEY:
        raise RuntimeError(
            "JINA_API_KEY is not configured. Set it in your .env file."
        )

    headers = {
        "Authorization": f"Bearer {settings.JINA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.JINA_EMBEDDING_MODEL,
        "task": task_type,
        "dimensions": EMBEDDING_DIM,
        "input": texts,
    }

    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.post(
                _JINA_ENDPOINT, headers=headers, json=payload, timeout=60
            )

            if response.status_code == 429 and attempt < _MAX_RETRIES - 1:
                wait = _BASE_BACKOFF_SECONDS * (attempt + 1)
                logger.warning(
                    "Jina embedding rate-limited, retrying in %ss (attempt %s/%s)",
                    wait, attempt + 1, _MAX_RETRIES,
                )
                time.sleep(wait)
                continue

            if response.status_code == 429:
                raise RuntimeError(
                    "JohnBot's free Jina embedding quota was hit. "
                    "Wait a minute and try again, or upload fewer/smaller files at once."
                )

            response.raise_for_status()

            data = sorted(response.json()["data"], key=lambda item: item["index"])
            matrix = np.array(
                [item["embedding"] for item in data],
                dtype=np.float32,
            )

            # Normalize defensively so cosine similarity == dot product,
            # matching what vector_store.py assumes.
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return matrix / norms

        except requests.HTTPError as exc:
            logger.error("Jina embedding request failed: %s", exc)
            raise RuntimeError(
                "JohnBot received an error response from Jina embeddings."
            ) from exc

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.error("Unexpected Jina embedding response: %s", exc)
            raise RuntimeError(
                "JohnBot received an unexpected response from Jina embeddings."
            ) from exc

    raise RuntimeError("JohnBot couldn't get embeddings from Jina after several retries.")


def _embed(texts: list[str], task_type: str) -> np.ndarray:
    """Embed texts in small batches to stay within free-tier rate limits."""

    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)

    batches = [texts[i:i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
    results = []

    for i, batch in enumerate(batches):
        results.append(_embed_batch(batch, task_type))
        if i < len(batches) - 1:
            time.sleep(0.5)  # gentle pacing between batches on the free tier

    return np.vstack(results)


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed code chunks for storage in the vector database.

    Documents use the retrieval.passage task type.
    """
    return _embed(texts, "retrieval.passage")


def embed_query(text: str) -> np.ndarray:
    """
    Embed a user's question for vector search.

    Queries use the retrieval.query task type.
    """
    return _embed([text], "retrieval.query")[0]
