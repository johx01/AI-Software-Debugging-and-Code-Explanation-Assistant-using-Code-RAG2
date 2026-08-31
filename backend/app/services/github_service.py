"""GitHub OAuth token exchange, repo listing, and repo ingestion into the RAG pipeline."""
import base64
import hashlib
import logging
import os

import requests

from app.config import settings, SUPPORTED_EXTENSIONS
from app.database.database import SessionLocal, FileRecord, RepoIngestJob
from app.rag import loader, chunker, embedder
from app.rag.vector_store import get_vector_store

logger = logging.getLogger("johnbot")

GITHUB_API = "https://api.github.com"


def exchange_code_for_token(code: str) -> str:
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_OAUTH_CALLBACK_URL,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise ValueError(f"GitHub token exchange failed: {data}")
    return token


def fetch_github_user(access_token: str) -> dict:
    resp = requests.get(
        f"{GITHUB_API}/user",
        headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def list_user_repos(access_token: str) -> list[dict]:
    repos = []
    page = 1
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    while True:
        resp = requests.get(
            f"{GITHUB_API}/user/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "affiliation": "owner,collaborator,organization_member"},
            timeout=15,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [
        {
            "full_name": r["full_name"],
            "name": r["name"],
            "owner": r["owner"]["login"],
            "private": r["private"],
            "default_branch": r["default_branch"],
        }
        for r in repos
    ]


def fetch_repo_tree(access_token: str, owner: str, repo: str, branch: str) -> list[dict]:
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}",
        headers=headers,
        params={"recursive": "1"},
        timeout=30,
    )
    resp.raise_for_status()
    tree = resp.json().get("tree", [])
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return [
        item
        for item in tree
        if item.get("type") == "blob"
        and os.path.splitext(item["path"])[1].lower() in SUPPORTED_EXTENSIONS
        and item.get("size", 0) <= max_size
        and item.get("size", 0) > 0
    ]


def fetch_file_content(access_token: str, owner: str, repo: str, path: str) -> bytes:
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}", headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("encoding") != "base64":
        raise ValueError(f"Unexpected encoding for {path}: {data.get('encoding')}")
    return base64.b64decode(data["content"])


def ingest_repo(job_id: int, access_token: str, owner: str, repo: str, branch: str):
    """Background task: fetch a repo's files and run them through the existing RAG pipeline."""
    db = SessionLocal()
    try:
        job = db.query(RepoIngestJob).filter(RepoIngestJob.id == job_id).first()
        if not job:
            return
        job.status = "fetching"
        db.commit()

        try:
            blobs = fetch_repo_tree(access_token, owner, repo, branch)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch tree for %s/%s", owner, repo)
            job.status = "error"
            job.error_message = str(exc)
            db.commit()
            return

        job.total_files = len(blobs)
        job.status = "processing"
        db.commit()

        user_dir = os.path.join(settings.UPLOAD_DIR, str(job.user_id), "github", repo)
        os.makedirs(user_dir, exist_ok=True)

        for blob in blobs:
            path = blob["path"]
            file_name = os.path.basename(path)
            try:
                content = fetch_file_content(access_token, owner, repo, path)
                content_hash = hashlib.sha256(content).hexdigest()

                existing = (
                    db.query(FileRecord)
                    .filter(FileRecord.user_id == job.user_id, FileRecord.content_hash == content_hash)
                    .first()
                )
                if existing and existing.status == "ready":
                    job.processed_files += 1
                    db.commit()
                    continue

                file_path = os.path.join(user_dir, path.replace("/", "__"))
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(content)

                record = FileRecord(
                    user_id=job.user_id,
                    file_name=file_name,
                    file_path=file_path,
                    status="processing",
                    content_hash=content_hash,
                    source="github",
                    repo_ingest_job_id=job.id,
                )
                db.add(record)
                db.commit()
                db.refresh(record)

                text = loader.read_file_text(record.file_path)
                language = loader.detect_language(record.file_name)
                record.language = language

                chunks = chunker.chunk_code(text, language)
                if chunks:
                    texts = [c["text"] for c in chunks]
                    embeddings = embedder.embed_texts(texts)
                    store = get_vector_store()
                    store.add_chunks(record.id, record.file_name, chunks, embeddings)
                    record.chunk_count = len(chunks)
                record.status = "ready"
                db.commit()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to ingest %s from %s/%s", path, owner, repo)
                job.error_message = f"{path}: {exc}"
            finally:
                job.processed_files += 1
                db.commit()

        job.status = "ready" if not job.error_message else "error"
        db.commit()
    finally:
        db.close()
