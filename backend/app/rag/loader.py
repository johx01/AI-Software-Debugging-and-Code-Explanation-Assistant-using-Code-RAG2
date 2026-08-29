"""Reads uploaded source files and detects their language."""
import os

EXT_LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".c": "c", ".cpp": "cpp", ".html": "html", ".css": "css",
    ".sql": "sql", ".json": "json", ".md": "markdown",
}


def detect_language(file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    return EXT_LANGUAGE_MAP.get(ext, "text")


def read_file_text(file_path: str) -> str:
    """Read a source file as plain text (never executed)."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
