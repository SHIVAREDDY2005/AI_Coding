from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_judge_service
from app.schemas.judge import JudgeExecutionRequest, JudgeExecutionResponse
from app.services.judge_service import JudgeService, JudgeServiceError

router = APIRouter()


@router.post("/evaluate", response_model=JudgeExecutionResponse, summary="Evaluate User Code against Test Cases")
def evaluate_code(
    request: JudgeExecutionRequest,
    judge_service: Annotated[JudgeService, Depends(get_judge_service)],
):
    try:
        return judge_service.evaluate_code(
            code=request.code,
            language=request.language,
            testcases=request.testcases,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except JudgeServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected evaluation error: {str(e)}")
