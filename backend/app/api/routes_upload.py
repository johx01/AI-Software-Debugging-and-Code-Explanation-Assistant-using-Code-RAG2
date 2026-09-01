from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database.database import get_db, User
from app.models.schemas import FileOut
from app.services.file_service import save_and_ingest
from app.utils.auth_utils import get_current_user


router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=List[FileOut])
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []

    for file in files:
        content = await file.read()
        record = save_and_ingest(
            db,
            current_user.id,
            file,
            content,
        )
        results.append(record)

    return [
        FileOut(
            id=r.id,
            file_name=r.file_name,
            language=r.language,
            status=r.status,
            chunk_count=r.chunk_count,
            created_at=r.created_at.isoformat(),
        )
        for r in results
    ]