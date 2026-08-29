from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database.database import get_db, User, UserSettings
from app.models.schemas import SettingsOut, SettingsUpdate
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_or_create(db: Session, user_id: int) -> UserSettings:
    row = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not row:
        row = UserSettings(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = _get_or_create(db, current_user.id)
    return SettingsOut(
        theme=row.theme, enter_to_send=bool(row.enter_to_send), show_sources=bool(row.show_sources),
        provider="Gemini", model=app_settings.GEMINI_MODEL,
    )


@router.put("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = _get_or_create(db, current_user.id)
    if payload.theme is not None:
        row.theme = payload.theme
    if payload.enter_to_send is not None:
        row.enter_to_send = int(payload.enter_to_send)
    if payload.show_sources is not None:
        row.show_sources = int(payload.show_sources)
    db.commit()
    db.refresh(row)
    return SettingsOut(
        theme=row.theme, enter_to_send=bool(row.enter_to_send), show_sources=bool(row.show_sources),
        provider="Gemini", model=app_settings.GEMINI_MODEL,
    )
