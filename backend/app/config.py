"""Centralized configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Agent Router (LLM provider)
# Gemini (LLM provider)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # Jina AI (embeddings)
    JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")
    JINA_EMBEDDING_MODEL: str = os.getenv(
        "JINA_EMBEDDING_MODEL",
        "jina-embeddings-v3",
    )

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

    # RAG
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2"))
    # Vercel's serverless filesystem is read-only outside of /tmp.
    _DEFAULT_DATA_DIR = "/tmp/data" if os.getenv("VERCEL") else "./data"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", f"{_DEFAULT_DATA_DIR}/uploads")
    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH", f"{_DEFAULT_DATA_DIR}/vector_store.pkl"
    )

    # Chat context
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))

    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_OAUTH_CALLBACK_URL: str = os.getenv(
        "GITHUB_OAUTH_CALLBACK_URL", "http://localhost:8000/github/callback"
    )


settings = Settings()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
    ".html", ".css", ".sql", ".json", ".md",
}

# Directories skipped when ingesting an uploaded folder (dependency/build/vcs noise).
EXCLUDED_DIR_NAMES = {
    "node_modules", ".git", ".svn", ".hg", "dist", "build", "out",
    "__pycache__", ".venv", "venv", "env", ".next", ".cache",
    "coverage", ".pytest_cache", ".idea", ".vscode", "target",
}
