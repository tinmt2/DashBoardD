"""
Vaccine import service: preview job, commit with duplicate protection, history.

Duplicate protection is two-layered:
  1. Application level: committable rows whose ``dedup_key`` already exists in
     ``vaccine_ticket_details`` (or earlier in the same batch) are skipped.
  2. Database level: ``vaccine_ticket_details.dedup_key`` is UNIQUE, so a
     concurrent commit of the same data fails atomically instead of inserting
     duplicates.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Set

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.vaccine import VaccineImportJob, VaccineTicketDetail
from app.repositories.ticket_repository import SQLiteTicketRepository
from app.schemas.ticket import CHAIN_VACCINE, TicketRecord
from app.services.vaccine.importer import ImportAnalysis, VaccineExcelImporter
from app.services.vaccine.parser import VaccineParseError

logger = logging.getLogger(__name__)

MAX_PREVIEW_ROWS = 1000
_SQLITE_IN_CHUNK = 500  # stay below SQLite's bound-parameter limit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _chunks(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


class VaccineImportService:
    def __init__(self, db: Session):
        self.db = db
        self.importer = VaccineExcelImporter()
        self.ticket_repo = SQLiteTicketRepository(db)

    # ----------------------------------------------------------------- helpers
    def _existing_keys(self, keys: List[str]) -> Set[str]:
        found: Set[str] = set()
        unique = list(dict.fromkeys(keys))
        for chunk in _chunks(unique, _SQLITE_IN_CHUNK):
            rows = (
                self.db.query(VaccineTicketDetail.dedup_key)
                .filter(VaccineTicketDetail.dedup_key.in_(chunk))
                .all()
            )
            found.update(r[0] for r in rows)
        return found

    def _get_job(self, import_id: str) -> VaccineImportJob | None:
        return self.db.query(VaccineImportJob).filter(VaccineImportJob.id == import_id).first()

    def _fail(self, job: VaccineImportJob, message: str) -> None:
        self.db.rollback()
        job = self._get_job(job.id) or job
        job.status = "FAILED"
        job.error_message = message
        self.db.add(job)
        self.db.commit()

    # ----------------------------------------------------------------- preview
    def preview(self, filename: str, content: bytes) -> Dict[str, Any]:
        job = VaccineImportJob(
            id=str(uuid.uuid4()),
            chain=CHAIN_VACCINE,
            filename=filename,
            created_at=_utcnow(),
            status="PARSING",
        )
        self.db.add(job)
        self.db.commit()

        try:
            analysis = self.importer.analyze(content, filename)
        except VaccineParseError as exc:
            self._fail(job, str(exc))
            return {"success": False, "importId": job.id, "status": "FAILED", "error_message": str(exc)}
        except Exception as exc:  # unexpected – never leave the job hanging
            logger.exception("[VACCINE_IMPORT] preview failed")
            msg = f"Lỗi không xác định khi đọc file: {exc}"
            self._fail(job, msg)
            return {"success": False, "importId": job.id, "status": "FAILED", "error_message": msg}

        try:
            committable = analysis.committable_rows
            imported_at = _utcnow()
            payload = []
            for r in committable:
                record = self.importer.mapper.build_ticket_record(r.mapped, imported_at)
                payload.append({
                    "dedup_key": r.dedup_key,
                    "record": record.model_dump(mode="json"),
                    "detail": self.importer.mapper.build_detail(r.mapped),
                })
            already_imported = len(self._existing_keys([p["dedup_key"] for p in payload]))

            job.file_format = analysis.file_format
            job.sheet_name = analysis.sheet_name
            job.total_rows = analysis.total_rows
            job.valid_rows = analysis.valid_rows
            job.warning_rows = analysis.warning_rows
            job.error_rows = analysis.error_rows
            job.preview_data = json.dumps(payload, ensure_ascii=False)
            job.status = "PREVIEW_READY"
            self.db.add(job)
            self.db.commit()
        except Exception as exc:
            logger.exception("[VACCINE_IMPORT] preview persistence failed")
            msg = f"Lỗi khi lưu preview: {exc}"
            self._fail(job, msg)
            return {"success": False, "importId": job.id, "status": "FAILED", "error_message": msg}

        logger.info(
            "[VACCINE_IMPORT] preview file=%s sheet=%s total=%d valid=%d warning=%d error=%d",
            filename, analysis.sheet_name, analysis.total_rows, analysis.valid_rows,
            analysis.warning_rows, analysis.error_rows,
        )
        return self._build_preview_response(job, analysis, len(payload), already_imported)

    def _build_preview_response(self, job: VaccineImportJob, analysis: ImportAnalysis,
                                committable: int, already_imported: int) -> Dict[str, Any]:
        mapper = self.importer.mapper
        preview_rows = []
        for r in analysis.rows[:MAX_PREVIEW_ROWS]:
            item = mapper.to_preview(r.mapped)
            item["status"] = r.status
            item["duplicateOf"] = r.duplicate_of
            item["issues"] = r.validation.errors + r.validation.warnings
            preview_rows.append(item)

        hm = analysis.header_mapping
        return {
            "success": True,
            "importId": job.id,
            "status": job.status,
            "chain": CHAIN_VACCINE,
            "fileName": analysis.file_name,
            "fileFormat": analysis.file_format,
            "sheetName": analysis.sheet_name,
            "availableSheets": analysis.available_sheets,
            "headerRowNumber": analysis.header_row_number,
            "totalRows": analysis.total_rows,
            "validRows": analysis.valid_rows,
            "warningRows": analysis.warning_rows,
            "errorRows": analysis.error_rows,
            "committableRows": committable,
            "duplicateInFileRows": analysis.duplicate_in_file_rows,
            "alreadyImportedRows": already_imported,
            "headers": analysis.headers,
            "columnMapping": hm.column_mapping,
            "missingOptionalColumns": hm.missing_optional,
            "unknownColumns": hm.unknown_headers,
            "previewRows": preview_rows,
            "previewTruncated": analysis.total_rows > MAX_PREVIEW_ROWS,
            "validationErrors": analysis.validation_errors,
            "warnings": analysis.warnings,
        }

    # ------------------------------------------------------------------ commit
    def commit(self, import_id: str) -> Dict[str, Any]:
        job = self._get_job(import_id)
        if not job:
            return {"success": False, "error_message": "Không tìm thấy phiên import Vaccine."}
        if job.status != "PREVIEW_READY":
            return {"success": False, "error_message": f"Không thể commit phiên import ở trạng thái {job.status}"}

        job.status = "COMMITTING"
        self.db.add(job)
        self.db.commit()

        try:
            payload = json.loads(job.preview_data) if job.preview_data else []
            existing = self._existing_keys([p["dedup_key"] for p in payload])

            committed_at = _utcnow()
            seen: Set[str] = set()
            records: List[TicketRecord] = []
            details: List[VaccineTicketDetail] = []
            duplicate_count = 0
            for p in payload:
                key = p["dedup_key"]
                d = p["detail"]
                rec_data = dict(p["record"])
                if key in existing or key in seen:
                    duplicate_count += 1
                    if key in existing:
                        existing_detail = self.db.query(VaccineTicketDetail).filter(VaccineTicketDetail.dedup_key == key).first()
                        if existing_detail:
                            if d.get("summary") is not None:
                                existing_detail.summary = d.get("summary")
                            if d.get("step_status") is not None:
                                existing_detail.step_status = d.get("step_status")
                            if d.get("step") is not None:
                                existing_detail.step = d.get("step")
                            if d.get("punishment") is not None:
                                existing_detail.punishment = d.get("punishment")
                            if d.get("vaccine_type") is not None:
                                existing_detail.vaccine_type = d.get("vaccine_type")
                            if d.get("violation_content") is not None:
                                existing_detail.violation_content = d.get("violation_content")
                            if rec_data.get("ticket_status") or rec_data.get("error_status"):
                                existing_ticket = self.db.query(Ticket).filter(Ticket.id == existing_detail.ticket_record_id).first()
                                if existing_ticket:
                                    if rec_data.get("ticket_status"):
                                        existing_ticket.ticket_status = rec_data.get("ticket_status")
                                    if rec_data.get("error_status"):
                                        existing_ticket.error_status = rec_data.get("error_status")
                    continue
                seen.add(key)

                rec_data["chain"] = CHAIN_VACCINE  # enforce, regardless of stored payload
                rec_data["imported_at"] = committed_at
                record = TicketRecord(**rec_data)
                records.append(record)

                details.append(VaccineTicketDetail(
                    ticket_record_id=record.id,
                    chain=CHAIN_VACCINE,
                    ticket_id=record.ticket_id,
                    dedup_key=key,
                    request_group=d.get("request_group"),
                    requester=d.get("requester"),
                    handler_department=d.get("handler_department"),
                    approver=d.get("approver"),
                    expected_completion_date=date.fromisoformat(d["expected_completion_date"]) if d.get("expected_completion_date") else None,
                    step=d.get("step"),
                    region=d.get("region"),
                    asm=d.get("asm"),
                    camera_count=d.get("camera_count"),
                    evidence_urls=d.get("evidence_urls"),
                    vaccine_type=d.get("vaccine_type"),
                    violation_content=d.get("violation_content"),
                    punishment=d.get("punishment"),
                    employee_raw=d.get("employee_raw"),
                    requested_date=date.fromisoformat(d["requested_date"]) if d.get("requested_date") else None,
                    step_status=d.get("step_status"),
                    summary=d.get("summary"),
                    video_urls=d.get("video_urls"),
                    injection_ticket_code=d.get("injection_ticket_code"),
                    import_id=job.id,
                    source_row=d.get("source_row"),
                ))

            self.ticket_repo.insert_many(records)
            if details:
                self.db.add_all(details)
                self.db.flush()

            job.new_rows = len(records)
            job.duplicate_rows = duplicate_count
            job.status = "COMPLETED"
            job.committed_at = committed_at
            job.preview_data = None
            self.db.add(job)
            self.db.commit()
        except IntegrityError:
            logger.exception("[VACCINE_IMPORT] duplicate detected at DB level")
            self._fail(job, "Phát hiện bản ghi trùng lặp khi ghi dữ liệu (có thể do import đồng thời). Vui lòng thử lại.")
            return {"success": False, "importId": import_id, "error_message": "Phát hiện bản ghi trùng lặp khi ghi dữ liệu."}
        except Exception as exc:
            logger.exception("[VACCINE_IMPORT] commit failed")
            self._fail(job, str(exc))
            return {"success": False, "importId": import_id, "error_message": str(exc)}

        logger.info(
            "[VACCINE_IMPORT] commit import_id=%s inserted=%d duplicates=%d",
            import_id, job.new_rows, job.duplicate_rows,
        )
        return {
            "success": True,
            "importId": job.id,
            "chain": CHAIN_VACCINE,
            "fileName": job.filename,
            "status": job.status,
            "summary": {
                "totalRows": job.total_rows,
                "committable": len(payload),
                "inserted": job.new_rows,
                "duplicates": job.duplicate_rows,
                "warningRows": job.warning_rows,
                "errorRows": job.error_rows,
            },
        }

    # ----------------------------------------------------------------- history
    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        jobs = (
            self.db.query(VaccineImportJob)
            .order_by(VaccineImportJob.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "importId": j.id,
                "chain": j.chain,
                "fileName": j.filename,
                "fileFormat": j.file_format,
                "sheetName": j.sheet_name,
                "createdAt": j.created_at.isoformat() if j.created_at else None,
                "committedAt": j.committed_at.isoformat() if j.committed_at else None,
                "status": j.status,
                "totalRows": j.total_rows or 0,
                "validRows": j.valid_rows or 0,
                "warningRows": j.warning_rows or 0,
                "errorRows": j.error_rows or 0,
                "successRows": j.new_rows or 0,
                "duplicateRows": j.duplicate_rows or 0,
                "errorMessage": j.error_message,
            }
            for j in jobs
        ]
