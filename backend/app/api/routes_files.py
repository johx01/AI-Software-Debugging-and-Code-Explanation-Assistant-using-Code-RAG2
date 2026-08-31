from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db, User, FileRecord
from app.models.schemas import FileOut
from app.services.file_service import delete_file
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=List[FileOut])
def list_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(FileRecord).filter(FileRecord.user_id == current_user.id).order_by(FileRecord.created_at.desc()).all()
    return [
        FileOut(
            id=r.id, file_name=r.file_name, language=r.language,
            status=r.status, chunk_count=r.chunk_count,
            created_at=r.created_at.isoformat(), source=r.source or "upload",
        )
        for r in records
    ]


@router.delete("/{file_id}")
def remove_file(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    delete_file(db, record)
    return {"detail": "File deleted"}
