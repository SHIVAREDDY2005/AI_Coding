from app.schemas.common import HealthResponse, ErrorResponse
from app.schemas.solution import (
    SolutionGenerateRequest,
    ExtractedSolutions,
    SolutionGenerateResponse,
)
from app.schemas.testcase import (
    TestCase,
    TestcaseGenerateRequest,
    TestcaseGenerateResponse,
    TestcaseValidateRequest,
    TestcaseValidateResponse,
)
from app.schemas.judge import (
    JudgeTestCaseResult,
    JudgeSummary,
    JudgeExecutionRequest,
    JudgeExecutionResponse,
)
from app.schemas.suggestion import SuggestionRequest, SuggestionResponse
from app.schemas.pipeline import PipelineRunRequest, PipelineRunResponse

__all__ = [
    "HealthResponse",
    "ErrorResponse",
    "SolutionGenerateRequest",
    "ExtractedSolutions",
    "SolutionGenerateResponse",
    "TestCase",
    "TestcaseGenerateRequest",
    "TestcaseGenerateResponse",
    "TestcaseValidateRequest",
    "TestcaseValidateResponse",
    "JudgeTestCaseResult",
    "JudgeSummary",
    "JudgeExecutionRequest",
    "JudgeExecutionResponse",
    "SuggestionRequest",
    "SuggestionResponse",
    "PipelineRunRequest",
    "PipelineRunResponse",
]
