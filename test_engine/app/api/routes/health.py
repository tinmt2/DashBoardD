from fastapi import APIRouter
from app.api.schemas.common import ApiResponse

router = APIRouter()

@router.get("/health", response_model=ApiResponse)
def health_check():
    return ApiResponse(
        success=True,
        status="ok",
        service="test-python-backend"
    )
