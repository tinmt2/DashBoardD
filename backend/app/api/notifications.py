from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter()

@router.get("")
def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    repo = NotificationRepository(db)
    items, total, unread_count = repo.get_all(limit=limit, skip=skip, unread_only=unread_only)
    return {
        "success": True,
        "total": total,
        "unread_count": unread_count,
        "items": [item.model_dump() for item in items]
    }

@router.post("")
def create_notification(req: NotificationCreate, db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    item = repo.create(req)
    return {
        "success": True,
        "item": item.model_dump()
    }

@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    item = repo.mark_as_read(notification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    return {
        "success": True,
        "item": item.model_dump()
    }

@router.post("/mark-all-read")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    count = repo.mark_all_as_read()
    return {
        "success": True,
        "updated": count
    }

@router.delete("/{notification_id}")
def delete_notification(notification_id: str, db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    success = repo.delete(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    return {
        "success": True
    }

@router.delete("")
def clear_all_notifications(db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    count = repo.clear_all()
    return {
        "success": True,
        "deleted": count
    }
