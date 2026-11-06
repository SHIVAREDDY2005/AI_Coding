from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service
from app.core.config import get_settings
from app.schemas.solution import SolutionGenerateRequest, SolutionGenerateResponse
from app.services.llm_service import LLMService, LLMServiceError

router = APIRouter()


@router.post("/generate", response_model=SolutionGenerateResponse, summary="Generate Reference Solutions")
def generate_reference_solutions(
    request: SolutionGenerateRequest,
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
):
    settings = get_settings()
    model_used = request.model or settings.GROQ_MODEL
    try:
        solutions = llm_service.generate_reference_solutions(
            problem=request.problem,
            model=request.model,
        )
        return SolutionGenerateResponse(
            brute_code=solutions.brute_code,
            optimal_code=solutions.optimal_code,
            model_used=model_used,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected generation failure: {str(e)}")
