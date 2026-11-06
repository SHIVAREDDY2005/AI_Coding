from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_judge_service
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.languages import get_supported_languages
from app.schemas.judge import JudgeExecutionRequest, JudgeExecutionResponse
from app.services.judge_service import JudgeService, JudgeServiceError

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent AI-powered competitive coding and evaluation platform backend.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root Endpoints (for convenience & health checking)
@app.get("/", tags=["Root"])
def root():
    return {
        "status": "ok",
        "message": f"{settings.PROJECT_NAME} v{settings.VERSION} is running",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok", "version": settings.VERSION}


@app.get("/languages", tags=["Root"])
def list_languages_root():
    return {"languages": get_supported_languages()}


# Backwards compatibility alias for /judge at root
@app.post("/judge", response_model=JudgeExecutionResponse, tags=["Root"])
def judge_root(
    req: JudgeExecutionRequest,
    judge_service: Annotated[JudgeService, Depends(get_judge_service)],
):
    try:
        return judge_service.evaluate_code(req.code, req.language, req.testcases)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except JudgeServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
