from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service
from app.schemas.suggestion import SuggestionRequest, SuggestionResponse
from app.services.llm_service import LLMService, LLMServiceError

router = APIRouter()


@router.post("/generate", response_model=SuggestionResponse, summary="Generate AI Mentoring Suggestions")
def generate_suggestion(
    request: SuggestionRequest,
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
):
    try:
        return llm_service.generate_suggestion(
            problem=request.problem,
            user_code=request.user_code,
            eval_result=request.eval_result,
            model=request.model,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected suggestion generation error: {str(e)}")
