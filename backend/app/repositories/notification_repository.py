import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.notification import SyncNotification
from app.schemas.notification import NotificationCreate, ChainSyncDetail, NotificationResponse

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_response(self, item: SyncNotification) -> NotificationResponse:
        chain_details_list = []
        if item.chain_details:
            try:
                raw = json.loads(item.chain_details)
                if isinstance(raw, list):
                    chain_details_list = [ChainSyncDetail(**d) for d in raw]
            except Exception:
                chain_details_list = []

        created_at_val = item.created_at
        if created_at_val and created_at_val.tzinfo is None:
            created_at_val = created_at_val.replace(tzinfo=timezone.utc)

        return NotificationResponse(
            id=item.id,
            title=item.title,
            status=item.status,
            sync_type=item.sync_type,
            start_date=item.start_date,
            end_date=item.end_date,
            total_new_errors=item.total_new_errors or 0,
            total_scanned=item.total_scanned or 0,
            total_duplicates=item.total_duplicates or 0,
            chain_details=chain_details_list,
            error_message=item.error_message,
            is_read=bool(item.is_read),
            created_at=created_at_val
        )

    def create(self, data: NotificationCreate) -> NotificationResponse:
        chain_details_json = None
        if data.chain_details:
            chain_details_json = json.dumps([d.model_dump() for d in data.chain_details], ensure_ascii=False)

        notification = SyncNotification(
            id=str(uuid.uuid4()),
            title=data.title,
            status=data.status,
            sync_type=data.sync_type,
            start_date=data.start_date,
            end_date=data.end_date,
            total_new_errors=data.total_new_errors,
            total_scanned=data.total_scanned,
            total_duplicates=data.total_duplicates,
            chain_details=chain_details_json,
            error_message=data.error_message,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return self._to_response(notification)

    def get_all(self, limit: int = 50, skip: int = 0, unread_only: bool = False) -> Tuple[List[NotificationResponse], int, int]:
        query = self.db.query(SyncNotification)
        total = query.count()
        unread_count = self.db.query(SyncNotification).filter(SyncNotification.is_read == False).count()

        if unread_only:
            query = query.filter(SyncNotification.is_read == False)

        items = query.order_by(SyncNotification.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_response(item) for item in items], total, unread_count

    def count_unread(self) -> int:
        return self.db.query(SyncNotification).filter(SyncNotification.is_read == False).count()

    def mark_as_read(self, notification_id: str) -> Optional[NotificationResponse]:
        item = self.db.query(SyncNotification).filter(SyncNotification.id == notification_id).first()
        if not item:
            return None
        item.is_read = True
        self.db.commit()
        self.db.refresh(item)
        return self._to_response(item)

    def mark_all_as_read(self) -> int:
        updated = self.db.query(SyncNotification).filter(SyncNotification.is_read == False).update({"is_read": True})
        self.db.commit()
        return updated

    def delete(self, notification_id: str) -> bool:
        item = self.db.query(SyncNotification).filter(SyncNotification.id == notification_id).first()
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def clear_all(self) -> int:
        count = self.db.query(SyncNotification).delete()
        self.db.commit()
        return count
