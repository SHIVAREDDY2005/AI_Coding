from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.embedding_service import EmbeddingService
from app.services.harness_service import HarnessService
from app.services.judge_service import JudgeService
from app.services.llm_service import LLMService
from app.services.similar_service import SimilarProblemsService
from app.services.validation_service import ValidationService


def get_harness_service() -> HarnessService:
    return HarnessService()


def get_judge_service(
    settings: Annotated[Settings, Depends(get_settings)],
    harness_service: Annotated[HarnessService, Depends(get_harness_service)],
) -> JudgeService:
    return JudgeService(settings=settings, harness_service=harness_service)


def get_llm_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMService:
    return LLMService(settings=settings)


def get_validation_service(
    judge_service: Annotated[JudgeService, Depends(get_judge_service)],
    harness_service: Annotated[HarnessService, Depends(get_harness_service)],
) -> ValidationService:
    return ValidationService(judge_service=judge_service, harness_service=harness_service)


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Process-wide singleton so all-MiniLM-L6-v2 is loaded only once."""
    return EmbeddingService()


def get_similar_service(
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
) -> SimilarProblemsService:
    return SimilarProblemsService(
        llm_service=llm_service,
        embedding_service=embedding_service,
    )
