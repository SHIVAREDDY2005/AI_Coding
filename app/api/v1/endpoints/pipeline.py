from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_judge_service, get_llm_service, get_validation_service
from app.schemas.pipeline import PipelineRunRequest, PipelineRunResponse
from app.services.judge_service import JudgeService, JudgeServiceError
from app.services.llm_service import LLMService, LLMServiceError
from app.services.validation_service import ValidationService

router = APIRouter()


@router.post("/run", response_model=PipelineRunResponse, summary="Execute Full Practice & Evaluation Pipeline")
def run_pipeline(
    request: PipelineRunRequest,
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    validation_service: Annotated[ValidationService, Depends(get_validation_service)],
    judge_service: Annotated[JudgeService, Depends(get_judge_service)],
):
    # 1. Reference Solutions
    try:
        solutions = llm_service.generate_reference_solutions(request.problem, request.model)
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate reference solutions: {str(e)}")

    # 2. Test Cases
    try:
        raw_testcases = llm_service.generate_testcases(request.problem, request.model)
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate test cases: {str(e)}")

    # 3. Sandboxed Validation
    try:
        val_resp = validation_service.validate_reference_solutions(
            brute_code=solutions.brute_code,
            optimal_code=solutions.optimal_code,
            testcases=raw_testcases,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

    if not val_resp.valid_testcases:
        raise HTTPException(
            status_code=422,
            detail="None of the generated test cases passed reference solution validation",
        )

    # 4. User Code Evaluation
    try:
        eval_resp = judge_service.evaluate_code(
            code=request.user_code,
            language=request.language,
            testcases=val_resp.valid_testcases,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except JudgeServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 5. Mentor Suggestion if any failures
    suggestion_resp = None
    if eval_resp.summary.verdict != "All Passed":
        try:
            suggestion_resp = llm_service.generate_suggestion(
                problem=request.problem,
                user_code=request.user_code,
                eval_result=eval_resp.model_dump(),
                model=request.model,
            )
        except Exception:
            pass

    return PipelineRunResponse(
        problem=request.problem,
        solutions=solutions,
        testcases_generated=len(raw_testcases),
        testcases_validated=len(val_resp.valid_testcases),
        evaluation=eval_resp,
        suggestion=suggestion_resp,
        success=eval_resp.summary.verdict == "All Passed",
        message="Evaluation completed successfully",
    )
