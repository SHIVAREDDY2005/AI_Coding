from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_similar_service
from app.schemas.similar import SimilarProblemRequest, SimilarProblemsResponse
from app.services.llm_service import LLMServiceError
from app.services.similar_service import SimilarProblemsService

router = APIRouter()


@router.post(
    "/similar",
    response_model=SimilarProblemsResponse,
    summary="Find Similar Problems on LeetCode, CodeChef, and Codeforces",
)
def find_similar_problems(
    request: SimilarProblemRequest,
    service: Annotated[SimilarProblemsService, Depends(get_similar_service)],
):
    try:
        return service.find_similar(
            problem=request.problem,
            refresh=request.refresh,
            platform=request.platform,
            solved_urls=request.solved_urls,
            attempted_urls=request.attempted_urls,
            exclude_solved=request.exclude_solved,
            target_difficulty=request.target_difficulty,
            model=request.model,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error finding similar problems: {str(e)}")
