from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.services.dashboard.vaccine_summary import VaccineDashboardSummary
from app.schemas.vaccine_dashboard import VaccineDashboardSummaryResponse

router = APIRouter(prefix="/vaccine", tags=["Vaccine Dashboard"])

@router.get("/summary", response_model=VaccineDashboardSummaryResponse)
def get_vaccine_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    service = VaccineDashboardSummary(db)
    data = service.get_summary(from_date=from_date, to_date=to_date)
    return VaccineDashboardSummaryResponse(
        success=True,
        data=data
    )
