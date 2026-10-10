import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
from datetime import datetime, timezone

from app.main import app
from app.core.database import Base, get_db
from app.models.ticket import Ticket

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Insert mock data
    tickets = [
        Ticket(id=str(uuid.uuid4()), chain="FPT_SHOP", ticket_id="T01", employee_name="NV1", employee_id="E01", error_status="ERROR", error_type="Thiáº¿u thÃ´ng tin", source="EXCEL", imported_at=datetime.now(timezone.utc)),
        Ticket(id=str(uuid.uuid4()), chain="FPT_SHOP", ticket_id="T02", employee_name="NV1", employee_id="E01", error_status="ERROR", error_type="Sai quy trÃ¬nh", source="EXCEL", imported_at=datetime.now(timezone.utc)),
        Ticket(id=str(uuid.uuid4()), chain="FPT_SHOP", ticket_id="T03", employee_name="NV2", employee_id="E02", error_status="PASS", error_type=None, source="EXCEL", imported_at=datetime.now(timezone.utc)),
    ]
    db.add_all(tickets)
    db.commit()
    db.close()
    yield

def test_get_dashboard_data():
    response = client.get("/api/fpt-shop/data")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 3
    assert len(data["data"]) == 3

def test_get_dashboard_summary():
    response = client.get("/api/fpt-shop/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    overview = data["overview"]
    assert overview["totalChecked"] == 3
    assert overview["totalErrors"] == 2
    assert overview["totalEmployees"] == 2
    assert overview["employeesWithErrors"] == 1
    assert round(overview["errorRate"]) == 67
    
    chain_stats = data["chainStats"]
    assert len(chain_stats) == 1
    assert chain_stats[0]["chain"] == "FPT Shop"
    assert chain_stats[0]["totalErrors"] == 2
    
    error_type_stats = data["errorTypeStats"]
    assert len(error_type_stats) == 2
    
    top_emp = data["topEmployees"]
    assert len(top_emp) == 1
    assert top_emp[0]["name"] == "NV1"
    assert top_emp[0]["totalErrors"] == 2

def test_empty_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.get("/api/fpt-shop/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]["totalChecked"] == 0
    assert data["overview"]["errorRate"] == 0.0

