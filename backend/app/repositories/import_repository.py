from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.import_job import ImportJob

class ImportRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, job: ImportJob) -> ImportJob:
        self.db.add(job)
        self.db.flush()
        return job
        
    def get_by_id(self, job_id: str) -> Optional[ImportJob]:
        return self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        
    def update(self, job: ImportJob) -> ImportJob:
        self.db.add(job)
        self.db.flush()
        return job
        
    def get_all(self) -> List[ImportJob]:
        return self.db.query(ImportJob).order_by(ImportJob.created_at.desc()).all()
