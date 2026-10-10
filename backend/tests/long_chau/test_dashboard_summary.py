import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.long_chau import LongChauTicketDetail
from app.schemas.ticket import CHAIN_LONG_CHAU
from app.services.dashboard.long_chau_summary import LongChauDashboardSummary

def test_01_empty_database(db_session: Session):
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert result.totalChecked == 0
    assert result.totalErrors == 0
    assert result.errorRate == 0

def test_02_with_records(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR", employee_name="A")
    t2 = Ticket(id="2", chain=CHAIN_LONG_CHAU, error_status="PASS")
    db_session.add_all([t1, t2])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert result.totalChecked == 2
    assert result.totalErrors == 1
    assert result.errorRate == 50.0

def test_03_04_employee(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR", employee_name="A")
    t2 = Ticket(id="2", chain=CHAIN_LONG_CHAU, error_status="ERROR", employee_name="")
    t3 = Ticket(id="3", chain=CHAIN_LONG_CHAU, error_status="ERROR")
    ld1 = LongChauTicketDetail(ticket_record_id="1", chain=CHAIN_LONG_CHAU, ticket_id="T1", dedup_key="D1", requester="A@fpt.com")
    ld2 = LongChauTicketDetail(ticket_record_id="2", chain=CHAIN_LONG_CHAU, ticket_id="T2", dedup_key="D2", requester="")
    ld3 = LongChauTicketDetail(ticket_record_id="3", chain=CHAIN_LONG_CHAU, ticket_id="T3", dedup_key="D3", requester="")
    db_session.add_all([t1, t2, t3, ld1, ld2, ld3])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert result.totalEmployees == 1
    assert len(result.employeeErrorRanking) == 1
    assert result.employeeErrorRanking[0].employeeName == "A"

def test_05_error_type(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR", error_type="E1")
    t2 = Ticket(id="2", chain=CHAIN_LONG_CHAU, error_status="ERROR", error_type="E1")
    t3 = Ticket(id="3", chain=CHAIN_LONG_CHAU, error_status="ERROR", error_type="E2")
    ld1 = LongChauTicketDetail(ticket_record_id="1", chain=CHAIN_LONG_CHAU, ticket_id="T1", dedup_key="D1", requester="A@fpt.com")
    ld2 = LongChauTicketDetail(ticket_record_id="2", chain=CHAIN_LONG_CHAU, ticket_id="T2", dedup_key="D2", requester="")
    ld3 = LongChauTicketDetail(ticket_record_id="3", chain=CHAIN_LONG_CHAU, ticket_id="T3", dedup_key="D3", requester="")
    db_session.add_all([t1, t2, t3, ld1, ld2, ld3])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert len(result.errorTypeStats) == 2
    assert result.errorTypeStats[0].errorType == "E1"
    assert result.errorTypeStats[0].count == 2

def test_07_shop_ranking(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR", shop_code="S1", shop_name="Shop 1")
    t2 = Ticket(id="2", chain=CHAIN_LONG_CHAU, error_status="ERROR", shop_code="S1", shop_name="Shop 1")
    db_session.add_all([t1, t2])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert len(result.shopErrorRanking) == 1
    assert result.shopErrorRanking[0].shopCode == "S1"
    assert result.shopErrorRanking[0].errorCount == 2

def test_08_region_ranking(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR")
    ld1 = LongChauTicketDetail(ticket_record_id="1", chain=CHAIN_LONG_CHAU, ticket_id="req1", dedup_key="d1", region="R1")
    db_session.add_all([t1, ld1])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert len(result.regionErrorStats) == 1
    assert result.regionErrorStats[0].region == "R1"
    assert result.regionErrorStats[0].errorCount == 1

def test_09_date_filter(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR", created_at=date(2026,10,1))
    t2 = Ticket(id="2", chain=CHAIN_LONG_CHAU, error_status="ERROR", created_at=date(2026,10,10))
    db_session.add_all([t1, t2])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary(from_date=date(2026,10,1), to_date=date(2026,10,5))
    assert result.totalChecked == 1

def test_10_data_isolation(db_session: Session):
    t1 = Ticket(id="1", chain=CHAIN_LONG_CHAU, error_status="ERROR")
    t2 = Ticket(id="2", chain="FPT_SHOP", error_status="ERROR")
    db_session.add_all([t1, t2])
    db_session.commit()
    
    service = LongChauDashboardSummary(db_session)
    result = service.get_summary()
    assert result.totalChecked == 1





