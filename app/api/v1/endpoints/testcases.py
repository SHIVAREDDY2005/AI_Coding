from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service, get_validation_service
from app.core.config import get_settings
from app.schemas.testcase import (
    TestcaseGenerateRequest,
    TestcaseGenerateResponse,
    TestcaseValidateRequest,
    TestcaseValidateResponse,
)
from app.services.llm_service import LLMService, LLMServiceError
from app.services.validation_service import ValidationService

router = APIRouter()


@router.post("/generate", response_model=TestcaseGenerateResponse, summary="Generate Candidate Test Cases")
def generate_testcases(
    request: TestcaseGenerateRequest,
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
):
    settings = get_settings()
    model_used = request.model or settings.GROQ_MODEL
    try:
        testcases = llm_service.generate_testcases(
            problem=request.problem,
            model=request.model,
        )
        return TestcaseGenerateResponse(
            testcases=testcases,
            count=len(testcases),
            model_used=model_used,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected testcase generation failure: {str(e)}")


@router.post("/validate", response_model=TestcaseValidateResponse, summary="Validate Test Cases via Judge0")
def validate_testcases(
    request: TestcaseValidateRequest,
    validation_service: Annotated[ValidationService, Depends(get_validation_service)],
):
    try:
        return validation_service.validate_reference_solutions(
            brute_code=request.brute_code,
            optimal_code=request.optimal_code,
            testcases=request.testcases,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
