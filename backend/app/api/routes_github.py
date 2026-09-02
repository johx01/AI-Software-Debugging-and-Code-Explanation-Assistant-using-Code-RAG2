from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database.database import get_db, User, GithubConnection, RepoIngestJob, Conversation
from app.models.schemas import (
    GithubConnectionOut,
    GithubConnectUrlOut,
    GithubRepoOut,
    GithubUrlIngestRequest,
    RepoIngestJobOut,
)
from app.services import github_service
from app.utils.auth_utils import (
    create_access_token,
    decode_token,
    get_current_user,
)


router = APIRouter(prefix="/api/github", tags=["github"])


def _get_connection(db: Session, user_id: int) -> GithubConnection:
    conn = (
        db.query(GithubConnection)
        .filter(GithubConnection.user_id == user_id)
        .first()
    )

    if not conn:
        raise HTTPException(
            status_code=400,
            detail="GitHub account not connected",
        )

    return conn


@router.get("/connect", response_model=GithubConnectUrlOut)
def connect(current_user: User = Depends(get_current_user)):
    if not app_settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured on the server",
        )

    # Reuse the user's own signed JWT as the OAuth `state` param
    # so the stateless callback can identify which user is connecting.
    state = create_access_token(current_user.id)

    query = urlencode(
        {
            "client_id": app_settings.GITHUB_CLIENT_ID,
            "redirect_uri": app_settings.GITHUB_OAUTH_CALLBACK_URL,
            "scope": "repo read:user",
            "state": state,
        }
    )

    return GithubConnectUrlOut(
        authorize_url=f"https://github.com/login/oauth/authorize?{query}"
    )


@router.get("/callback")
def callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    user_id = decode_token(state)

    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired GitHub OAuth state",
        )

    try:
        access_token = github_service.exchange_code_for_token(code)
        gh_user = github_service.fetch_github_user(access_token)
    except Exception as exc:  # noqa: BLE001
        return RedirectResponse(
            f"{app_settings.FRONTEND_ORIGIN}/settings?github_error={exc}"
        )

    conn = (
        db.query(GithubConnection)
        .filter(GithubConnection.user_id == user_id)
        .first()
    )

    if not conn:
        conn = GithubConnection(user_id=user_id)
        db.add(conn)

    conn.github_user_id = str(gh_user["id"])
    conn.github_login = gh_user["login"]
    conn.access_token = access_token

    db.commit()

    return RedirectResponse(
        f"{app_settings.FRONTEND_ORIGIN}/settings?github=connected"
    )


@router.get("/connection", response_model=GithubConnectionOut)
def get_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(GithubConnection)
        .filter(GithubConnection.user_id == current_user.id)
        .first()
    )

    if not conn:
        return GithubConnectionOut(connected=False)

    return GithubConnectionOut(
        connected=True,
        github_login=conn.github_login,
        connected_at=conn.connected_at.isoformat(),
    )


@router.delete("/connection")
def disconnect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(GithubConnection)
        .filter(GithubConnection.user_id == current_user.id)
        .first()
    )

    if conn:
        db.delete(conn)
        db.commit()

    return {"detail": "GitHub account disconnected"}


@router.get("/repos", response_model=list[GithubRepoOut])
def list_repos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = _get_connection(db, current_user.id)

    repos = github_service.list_user_repos(conn.access_token)

    return [GithubRepoOut(**r) for r in repos]


def _job_out(job: RepoIngestJob) -> RepoIngestJobOut:
    return RepoIngestJobOut(
        id=job.id,
        repo_full_name=job.repo_full_name,
        status=job.status,
        total_files=job.total_files,
        processed_files=job.processed_files,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        conversation_id=job.conversation_id,
    )


@router.post("/ingest-url", response_model=RepoIngestJobOut)
def ingest_url(
    payload: GithubUrlIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest any GitHub repo URL (public, or private if the user's own token can see it) —
    used for repo links pasted directly into chat, without requiring a GitHub connection."""
    parsed = github_service.find_github_repo_url(payload.url)
    if not parsed:
        raise HTTPException(status_code=400, detail="No GitHub repository URL found")

    if payload.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    conn = (
        db.query(GithubConnection)
        .filter(GithubConnection.user_id == current_user.id)
        .first()
    )
    access_token = conn.access_token if conn else None

    try:
        repo_meta = github_service.fetch_repo_meta(parsed["owner"], parsed["repo"], access_token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not reach GitHub: {exc}")

    branch = parsed["branch"] or repo_meta["default_branch"]

    job = RepoIngestJob(
        user_id=current_user.id,
        repo_full_name=repo_meta["full_name"],
        status="pending",
        conversation_id=payload.conversation_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        github_service.ingest_repo,
        job.id,
        access_token,
        parsed["owner"],
        parsed["repo"],
        branch,
        payload.conversation_id,
    )

    return _job_out(job)


@router.post(
    "/repos/{owner}/{repo}/ingest",
    response_model=RepoIngestJobOut,
)
def ingest_repo(
    owner: str,
    repo: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = _get_connection(db, current_user.id)

    repos = {
        r["full_name"]: r
        for r in github_service.list_user_repos(conn.access_token)
    }

    full_name = f"{owner}/{repo}"
    repo_meta = repos.get(full_name)

    if not repo_meta:
        raise HTTPException(
            status_code=404,
            detail="Repository not found or not accessible",
        )

    job = RepoIngestJob(
        user_id=current_user.id,
        repo_full_name=full_name,
        status="pending",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        github_service.ingest_repo,
        job.id,
        conn.access_token,
        owner,
        repo,
        repo_meta["default_branch"],
    )

    return _job_out(job)


@router.get("/jobs/{job_id}", response_model=RepoIngestJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = (
        db.query(RepoIngestJob)
        .filter(
            RepoIngestJob.id == job_id,
            RepoIngestJob.user_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return _job_out(job)