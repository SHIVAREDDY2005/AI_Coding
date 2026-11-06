from fastapi import APIRouter
from app.core.config import get_settings
from app.core.languages import get_supported_languages
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
def get_health():
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.VERSION)


@router.get("/languages", summary="List Supported Execution Languages")
def list_languages():
    return {"languages": get_supported_languages()}
