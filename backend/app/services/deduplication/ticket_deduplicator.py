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
        
        existing_map = {f"{t.ticket_id}_{t.error_type}_{t.error_reason}": t for t in existing_db_records}
        
        processed_in_batch = set()

        for record in records:
            if not record.ticket_id:
                new_records.append(record)
                continue
                
            identity = self._get_identity(record)
                
            if identity in existing_map:
                existing_ticket = existing_map[identity]
                # Check if fields have updated (e.g. ticket_status, note, employee_name)
                is_updated = False
                if record.ticket_status and record.ticket_status != existing_ticket.ticket_status:
                    existing_ticket.ticket_status = record.ticket_status
                    is_updated = True
                if record.note and record.note != existing_ticket.note:
                    existing_ticket.note = record.note
                    is_updated = True
                if record.employee_name and record.employee_name != existing_ticket.employee_name:
                    existing_ticket.employee_name = record.employee_name
                    is_updated = True
                
                if is_updated:
                    updated_count += 1
                else:
                    duplicate_count += 1
            elif identity in processed_in_batch:
                duplicate_count += 1
            else:
                new_records.append(record)
                processed_in_batch.add(identity)
                
        new_count = len(new_records)
        return new_records, new_count, duplicate_count, updated_count
