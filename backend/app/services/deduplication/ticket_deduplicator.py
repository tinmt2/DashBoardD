from typing import List, Tuple
from app.schemas.ticket import TicketRecord
from app.repositories.ticket_repository import SQLiteTicketRepository
from app.models.ticket import Ticket

class TicketDeduplicator:
    def __init__(self, repository: SQLiteTicketRepository):
        self.repository = repository

    def _get_identity(self, record):
        return f"{record.ticket_id}_{record.error_type}_{record.error_reason}"

    def deduplicate(self, records: List[TicketRecord]) -> Tuple[List[TicketRecord], int, int, int]:
        """
        Returns: (new_records, new_count, duplicate_count, updated_count)
        """
        new_records = []
        duplicate_count = 0
        updated_count = 0
        
        incoming_ids = [r.ticket_id for r in records if r.ticket_id]
        
        existing_db_records = self.repository.db.query(Ticket).filter(
            Ticket.chain == "FPT_SHOP",
            Ticket.ticket_id.in_(incoming_ids)
        ).all()
        
        existing_identities = {f"{t.ticket_id}_{t.error_type}_{t.error_reason}" for t in existing_db_records}
        
        processed_in_batch = set()

        for record in records:
            if not record.ticket_id:
                new_records.append(record)
                continue
                
            identity = self._get_identity(record)
                
            if identity in existing_identities or identity in processed_in_batch:
                duplicate_count += 1
            else:
                new_records.append(record)
                processed_in_batch.add(identity)
                
        new_count = len(new_records)
        return new_records, new_count, duplicate_count, updated_count
