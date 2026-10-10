from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.services.dashboard.long_chau_summary import LongChauDashboardSummary
from app.schemas.long_chau_dashboard import LongChauDashboardSummaryResponse

router = APIRouter(prefix="/long-chau", tags=["Long Châu Dashboard"])

@router.get("/summary", response_model=LongChauDashboardSummaryResponse)
def get_long_chau_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    service = LongChauDashboardSummary(db)
    data = service.get_summary(from_date=from_date, to_date=to_date)
    return LongChauDashboardSummaryResponse(
        success=True,
        data=data
    )
