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
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./data/vector_store.pkl")

    # Chat context
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))

    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


settings = Settings()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
    ".html", ".css", ".sql", ".json", ".md",
}
