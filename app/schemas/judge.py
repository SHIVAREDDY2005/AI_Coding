from typing import Any, Optional, Union
from pydantic import BaseModel, Field, model_validator
from app.schemas.testcase import TestCase


class JudgeTestCaseResult(BaseModel):
    testcase: int
    status: str
    passed: bool
    input: Optional[Any] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    raw: Optional[str] = None
    time: Optional[str] = None
    memory: Optional[int] = None


class JudgeSummary(BaseModel):
    passed: int
    total: int
    ran: int
    verdict: str


class JudgeExecutionRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code to evaluate")
    language: Optional[Union[int, str]] = Field(default=None, description="Language name, alias, or Judge0 integer ID")
    language_id: Optional[Union[int, str]] = Field(default=None, description="Alias for language")
    testcases: list[TestCase] = Field(..., min_length=1, description="List of test cases")

    @model_validator(mode="before")
    @classmethod
    def resolve_language_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            lang = values.get("language") or values.get("language_id")
            if not lang:
                raise ValueError("Field 'language' or 'language_id' is required")
            values["language"] = lang
            values["language_id"] = lang
        return values


class JudgeExecutionResponse(BaseModel):
    summary: JudgeSummary
    results: list[JudgeTestCaseResult]
    detected_function: str
    language_id: int
