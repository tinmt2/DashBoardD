import logging
from typing import List, Dict, Set
from datetime import datetime, date
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.long_chau import LongChauTicketDetail
from app.repositories.ticket_repository import SQLiteTicketRepository
from app.schemas.ticket import CHAIN_LONG_CHAU, TicketRecord
from app.services.long_chau.importer import build_dedup_key

logger = logging.getLogger(__name__)

def save_long_chau_api_records(db: Session, records: List[Dict]):
    committed_at = datetime.utcnow()
    seen: Set[str] = set()
    
    # Pre-fetch existing dedup keys from LongChauTicketDetail
    # To do this safely, we query all dedup_keys in the DB
    existing_keys = {row[0] for row in db.query(LongChauTicketDetail.dedup_key).all() if row[0]}
    
    inserted_count = 0
    duplicate_count = 0
    
    for r in records:
        ticket_id = str(r.get("TicketID") or "")
        if ticket_id.startswith("ro_ta_"):
            tc = str(r.get("TicketContent") or "")
            if " - " in tc:
                ticket_id = tc.split(" - ")[0].strip()
                
        error_type = str(r.get("TypeError") or "")
        shop_code = str(r.get("ShopCode") or "")
        
        if not ticket_id:
            ticket_id = f"UNKNOWN-{str(r.get('_id', ''))[:8]}"
            
        dedup_key = build_dedup_key(CHAIN_LONG_CHAU, ticket_id, error_type, str(r.get("Description") or ""))
        
        if dedup_key in existing_keys or dedup_key in seen:
            duplicate_count += 1
            continue
            
        seen.add(dedup_key)
        
        created_at_str = str(r.get("Created At") or r.get("createdAt") or "")
        dt_created = None
        if created_at_str:
            try:
                dt_created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except:
                pass
                
        error_status = "ERROR"
        
        requester = str(r.get("Người tạo") or r.get("CreatedByEmail") or "")
        
        rec = TicketRecord(
            id=str(uuid.uuid4()),
            chain=CHAIN_LONG_CHAU,
            ticket_id=ticket_id,
            employee_id=None,
            employee_name=None,
            shop_code=shop_code,
            shop_name=str(r.get("ShopName") or ""),
            created_at=dt_created,
            checked_at=dt_created,
            error_status=error_status,
            error_type=error_type,
            error_reason=str(r.get("Description") or ""),
            ticket_status="Hoàn tất" if r.get("Approve") else "Đang xử lý",
            note=str(r.get("Description") or ""),
            source="INTERNAL_WEB",
            imported_at=committed_at
        )
        
        # Save record
        repo = SQLiteTicketRepository(db)
        repo.insert_many([rec])
        
        # Detail

        # Try to extract optional fields that might exist in some rows
        employee_raw = str(r.get("Nhân viên vi phạm") or r.get("Employee") or r.get("Staff") or r.get("NhanVien") or r.get("Nhân viên") or "")
        request_group = str(r.get("Nhóm yêu cầu") or r.get("RequestGroup") or r.get("Nhóm Yêu Cầu") or "")
        handler_department = str(r.get("Phòng ban xử lý") or r.get("HandlerDepartment") or r.get("Phòng Ban Xử Lý") or "")
        expected_date_str = str(r.get("Ngày dự kiến hoàn thành") or r.get("ExpectedDate") or r.get("Ngày Dự Kiến Hoàn Thành") or "")
        expected_date = None
        if expected_date_str:
            try:
                expected_date = datetime.fromisoformat(expected_date_str.replace("Z", "+00:00")).date()
            except:
                pass

        detail = LongChauTicketDetail(
            ticket_record_id=rec.id,
            chain=CHAIN_LONG_CHAU,
            ticket_id=ticket_id,
            dedup_key=dedup_key,
            request_group=request_group if request_group else None,
            requester=requester,
            handler_department=handler_department if handler_department else None,
            approver=str(r.get("UserApprove") or ""),
            expected_completion_date=expected_date,
            step=str(r.get("Step") or ""),
            region=str(r.get("Region") or ""),
            asm=str(r.get("ASM") or r.get("Asm") or r.get("asm") or ""),
            camera_count=str(r.get("NumberCameras", [""])[0]) if isinstance(r.get("NumberCameras"), list) and r.get("NumberCameras") else None,
            evidence_urls=",".join([f.get("url", "") for f in r.get("File", [])]) if isinstance(r.get("File"), list) else None,
            employee_raw=employee_raw if employee_raw else None,
            requested_date=dt_created.date() if dt_created else None,
            step_status=None,
            import_id=f"api_{committed_at.strftime('%Y%m%d%H%M%S')}",
            source_row=0
        )
        
        db.add(detail)
        try:
            db.commit()
            inserted_count += 1
        except IntegrityError:
            db.rollback()
            duplicate_count += 1
            
    return inserted_count, duplicate_count
