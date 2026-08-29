"""
Gemini embedding service.

This module is responsible only for converting code/query text
into embedding vectors for the RAG vector store. It uses Google's
free-tier Gemini Embedding API (no paid key required) via the
same google-genai SDK already used by llm_service.py.
"""

import logging
import time

import numpy as np
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings

logger = logging.getLogger("johnbot")

# gemini-embedding-001 supports flexible output dimensions (768-3072).
# 768 keeps requests small and fast, and matches Matryoshka-trained
# truncation so quality stays strong while staying well inside the
# free tier's token-per-minute budget.
EMBEDDING_DIM = 768

# Free tier is rate-limited (roughly 100 requests/min, ~1000/day as of
# early 2026). Batch chunks together and add small gaps between calls
# so a big file upload doesn't immediately trip 429s.
_BATCH_SIZE = 20
_MAX_RETRIES = 5
_BASE_BACKOFF_SECONDS = 5

_client = None


def _get_client():
    global _client
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Set it in your .env file."
        )
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _embed_batch(texts: list[str], task_type: str) -> np.ndarray:
    """Embed a single batch of texts, retrying on rate limits."""

    client = _get_client()

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIM,
                ),
            )

            matrix = np.array(
                [e.values for e in response.embeddings],
                dtype=np.float32,
            )

            # gemini-embedding-001 outputs are not pre-normalized when a
            # non-default output_dimensionality is requested, so
            # normalize here to keep cosine similarity == dot product,
            # matching what vector_store.py assumes.
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return matrix / norms

        except ClientError as exc:
            status = getattr(exc, "code", None)
            if status == 429 and attempt < _MAX_RETRIES - 1:
                wait = _BASE_BACKOFF_SECONDS * (attempt + 1)
                logger.warning(
                    "Gemini embedding rate-limited, retrying in %ss (attempt %s/%s)",
                    wait, attempt + 1, _MAX_RETRIES,
                )
                time.sleep(wait)
                continue
            logger.error("Gemini embedding request failed: %s", exc)
            raise RuntimeError(
                "JohnBot's free Gemini embedding quota was hit. "
                "Wait a minute and try again, or upload fewer/smaller files at once."
            ) from exc

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.error("Unexpected Gemini embedding response: %s", exc)
            raise RuntimeError(
                "JohnBot received an unexpected response from Gemini embeddings."
            ) from exc

    raise RuntimeError("JohnBot couldn't get embeddings from Gemini after several retries.")


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

    Documents use the RETRIEVAL_DOCUMENT task type.
    """
    return _embed(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> np.ndarray:
    """
    Embed a user's question for vector search.

    Queries use the RETRIEVAL_QUERY task type.
    """
    return _embed([text], "RETRIEVAL_QUERY")[0]
