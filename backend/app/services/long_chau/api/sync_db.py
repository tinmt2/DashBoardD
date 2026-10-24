import logging
from typing import List, Dict, Set
from datetime import datetime, date
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.long_chau import LongChauTicketDetail
from app.repositories.ticket_repository import SQLiteTicketRepository
from app.schemas.ticket import CHAIN_LONG_CHAU, TicketRecord
from app.services.long_chau.importer import build_dedup_key

logger = logging.getLogger(__name__)

def save_long_chau_api_records(db: Session, records: List[Dict]):
    committed_at = datetime.utcnow()
    seen: Set[str] = set()
    
    # Pre-fetch existing dedup keys from LongChauTicketDetail
    existing_keys = {row[0] for row in db.query(LongChauTicketDetail.dedup_key).all() if row[0]}
    
    inserted_count = 0
    duplicate_count = 0
    updated_count = 0
    
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
        
        if dedup_key in seen:
            duplicate_count += 1
            continue
            
        seen.add(dedup_key)

        # Determine ticket_status & step_status accurately
        raw_status = str(
            r.get("TRẠNG THÁI") or 
            r.get("Trạng thái") or 
            r.get("Trạng Thái") or 
            r.get("Status") or 
            r.get("status") or 
            r.get("TicketStatus") or 
            ""
        ).strip()
        step = str(r.get("Step") or "").strip()
        
        if raw_status in ["Hoàn tất", "Đang xử lý"]:
            ticket_status = raw_status
        elif step in ["1", "2", "3"]:
            ticket_status = "Đang xử lý"
        elif step == "4":
            ticket_status = "Hoàn tất" if r.get("Approve") else "Đang xử lý"
        else:
            ticket_status = "Hoàn tất" if r.get("Approve") else "Đang xử lý"

        step_status = str(
            r.get("TRẠNG THÁI BƯỚC") or 
            r.get("Trạng thái bước") or 
            r.get("Trạng Thái Bước") or 
            r.get("StepStatus") or 
            r.get("Step_Status") or 
            ""
        ).strip() or None
        
        if not step_status:
            if step == "3":
                step_status = "Đang xử lý"
            elif step == "4":
                step_status = "Đã trả lời"
            elif step == "2":
                step_status = "Chờ xử lý"

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
        approver = str(r.get("UserApprove") or "")
        region = str(r.get("Region") or "")
        asm = str(r.get("ASM") or r.get("Asm") or r.get("asm") or "")

        # If already exists in DB, update latest status, step, and metadata
        if dedup_key in existing_keys:
            duplicate_count += 1
            detail = db.query(LongChauTicketDetail).filter(LongChauTicketDetail.dedup_key == dedup_key).first()
            if detail:
                if step:
                    detail.step = step
                if step_status:
                    detail.step_status = step_status
                if approver:
                    detail.approver = approver
                if expected_date:
                    detail.expected_completion_date = expected_date
                if request_group and not detail.request_group:
                    detail.request_group = request_group
                if handler_department and not detail.handler_department:
                    detail.handler_department = handler_department
                if employee_raw and not detail.employee_raw:
                    detail.employee_raw = employee_raw
                if region and not detail.region:
                    detail.region = region
                if asm and not detail.asm:
                    detail.asm = asm
                
                ticket = db.query(Ticket).filter(Ticket.id == detail.ticket_record_id).first()
                if ticket:
                    if ticket_status and ticket.ticket_status != ticket_status:
                        ticket.ticket_status = ticket_status
                        updated_count += 1
                    if shop_code and not ticket.shop_code:
                        ticket.shop_code = shop_code
                    if r.get("ShopName") and not ticket.shop_name:
                        ticket.shop_name = str(r.get("ShopName"))
            continue
        
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
            ticket_status=ticket_status,
            note=str(r.get("Description") or ""),
            source="INTERNAL_WEB",
            imported_at=committed_at
        )
        
        # Save record
        repo = SQLiteTicketRepository(db)
        repo.insert_many([rec])
        
        # Detail
        detail = LongChauTicketDetail(
            ticket_record_id=rec.id,
            chain=CHAIN_LONG_CHAU,
            ticket_id=ticket_id,
            dedup_key=dedup_key,
            request_group=request_group if request_group else None,
            requester=requester,
            handler_department=handler_department if handler_department else None,
            approver=approver if approver else None,
            expected_completion_date=expected_date,
            step=step if step else None,
            region=region if region else None,
            asm=asm if asm else None,
            camera_count=str(r.get("NumberCameras", [""])[0]) if isinstance(r.get("NumberCameras"), list) and r.get("NumberCameras") else None,
            evidence_urls=",".join([f.get("url", "") for f in r.get("File", [])]) if isinstance(r.get("File"), list) else None,
            employee_raw=employee_raw if employee_raw else None,
            requested_date=dt_created.date() if dt_created else None,
            step_status=step_status,
            import_id=f"api_{committed_at.strftime('%Y%m%d%H%M%S')}",
            source_row=0
        )
        
        db.add(detail)
        try:
            db.commit()
            inserted_count += 1
            existing_keys.add(dedup_key)
        except IntegrityError:
            db.rollback()
            duplicate_count += 1
            
    db.commit()
    logger.info(f"[LONG_CHAU_SYNC] inserted={inserted_count}, updated={updated_count}, duplicates={duplicate_count}")
    return inserted_count, duplicate_count
