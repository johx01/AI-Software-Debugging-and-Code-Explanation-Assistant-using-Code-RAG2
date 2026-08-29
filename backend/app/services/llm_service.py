"""
Centralized Gemini LLM service.

This is the only place in the application that talks
to the Gemini API.
"""

import logging

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger("johnbot")


SYSTEM_PROMPT = """You are JohnBot, an AI assistant that helps developers understand and debug their own codebase.

Rules:
- Use the retrieved code context below as your primary source of truth.
- Answer based on the provided context; do not invent files, functions, or code that isn't shown to you.
- When explaining code, describe what it does, how it works, and any important details.
- When asked about bugs, identify the likely problem, explain why it happens, and suggest a fix.
- Mention relevant file names and line ranges when the context includes them.
- Clearly distinguish existing code (from context) from code you are suggesting as a fix.
- If the retrieved context is insufficient to answer confidently, say so honestly instead of guessing.
"""


def build_context(chunks) -> str:
    if not chunks:
        return "(No relevant code was retrieved. The user may not have uploaded relevant files yet.)"

    parts = []

    for c in chunks:
        parts.append(
            f"### {c.file_name} "
            f"(lines {c.start_line}-{c.end_line})\n"
            f"```\n{c.text}\n```"
        )

    return "\n\n".join(parts)


def generate_answer(
    question: str,
    chunks,
    recent_history: list[dict],
) -> str:
    """
    Makes one Gemini request per user question.
    """

    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Set it in your .env file."
        )

    context = build_context(chunks)

    history_text = ""

    if recent_history:
        history_parts = []

        for message in recent_history:
            role = message.get("role", "user").upper()
            content = message.get("content", "")
            history_parts.append(f"{role}: {content}")

        history_text = (
            "\n\nRecent conversation:\n"
            + "\n".join(history_parts)
        )

    prompt = f"""{SYSTEM_PROMPT}

Retrieved code context:

{context}

{history_text}

Current question:
{question}
"""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text

    except Exception as exc:
        logger.error("Gemini request failed: %s", exc)
        raise RuntimeError(
            "JohnBot couldn't reach Gemini. Check your Gemini API key and network."
        ) from exc