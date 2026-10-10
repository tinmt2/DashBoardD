from typing import Protocol, List, Optional
from app.schemas.ticket import TicketRecord

class TicketRepository(Protocol):
    def insert_many(self, records: List[TicketRecord]) -> None:
        ...

    def get_all(self) -> List[TicketRecord]:
        ...

    def find_by_ticket_id(self, ticket_id: str) -> Optional[TicketRecord]:
        ...

    def get_summary(self):
        ...
