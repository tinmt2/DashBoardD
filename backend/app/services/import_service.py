import uuid
import json
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.import_job import ImportJob
from app.schemas.ticket import TicketRecord
from app.services.importers.fpt_shop.importer import FPTShopExcelImporter
from app.repositories.import_repository import ImportRepository
from app.repositories.ticket_repository import SQLiteTicketRepository
from app.services.deduplication.ticket_deduplicator import TicketDeduplicator

class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportRepository(db)
        self.ticket_repo = SQLiteTicketRepository(db)
        self.excel_importer = FPTShopExcelImporter()
        self.deduplicator = TicketDeduplicator(self.ticket_repo)

    def preview(self, filename: str, file_content: bytes) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        job = ImportJob(
            id=job_id,
            filename=filename,
            created_at=datetime.now(timezone.utc),
            status="PARSING"
        )
        self.import_repo.create(job)
        self.db.commit()

        try:
            valid_records, errors, mapping = self.excel_importer.process_file(file_content)
            
            job.total_rows = len(valid_records) + len(errors)
            job.valid_rows = len(valid_records)
            job.invalid_rows = len(errors)
            job.status = "PREVIEW_READY"
            
            # Serialize valid records to JSON to store temporarily
            records_dicts = [r.model_dump(mode='json') for r in valid_records]
            job.preview_data = json.dumps(records_dicts)
            
            self.import_repo.update(job)
            self.db.commit()

            return {
                "success": True,
                "import_id": job.id,
                "filename": job.filename,
                "status": job.status,
                "summary": {
                    "total_rows": job.total_rows,
                    "valid_rows": job.valid_rows,
                    "invalid_rows": job.invalid_rows
                },
                "mapping": mapping,
                "records": records_dicts,
                "errors": errors
            }

        except Exception as e:
            self.db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            self.import_repo.update(job)
            self.db.commit()
            return {
                "success": False,
                "import_id": job.id,
                "status": "FAILED",
                "error_message": str(e)
            }

    def commit(self, import_id: str) -> Dict[str, Any]:
        job = self.import_repo.get_by_id(import_id)
        if not job:
            return {"success": False, "error_message": "Import job not found."}
            
        if job.status not in ["PREVIEW_READY", "WAITING_CONFIRMATION"]:
            return {"success": False, "error_message": f"Cannot commit job in status {job.status}"}

        job.status = "COMMITTING"
        self.import_repo.update(job)
        self.db.commit()

        try:
            # Parse preview_data back to models
            if not job.preview_data:
                records = []
            else:
                raw_records = json.loads(job.preview_data)
                records = [TicketRecord(**r) for r in raw_records]

            new_records, new_count, duplicate_count, updated_count = self.deduplicator.deduplicate(records)

            self.ticket_repo.insert_many(new_records)
            
            job.new_rows = new_count
            job.duplicate_rows = duplicate_count
            # job.updated_rows = updated_count # Schema missing this, but we don't have updates yet
            job.status = "COMPLETED"
            # Optional: clear preview data to save space
            job.preview_data = None
            
            self.import_repo.update(job)
            self.db.commit()
            
            return {
                "success": True,
                "import_id": job.id,
                "summary": {
                    "total": job.valid_rows,
                    "new": new_count,
                    "duplicate": duplicate_count,
                    "updated": updated_count,
                    "invalid": job.invalid_rows
                }
            }
            
        except Exception as e:
            self.db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            self.import_repo.update(job)
            self.db.commit()
            return {
                "success": False,
                "import_id": job.id,
                "error_message": str(e)
            }
