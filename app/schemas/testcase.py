from typing import Any, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    input: Any = Field(..., description="Test case input (can be primitive, list, or dict)")
    expected_output: Any = Field(..., description="Expected output corresponding to input")


class TestcaseGenerateRequest(BaseModel):
    problem: str = Field(..., min_length=5, description="Problem description")
    model: Optional[str] = Field(default=None, description="Groq model override")


class TestcaseGenerateResponse(BaseModel):
    testcases: list[TestCase]
    count: int
    model_used: str


class TestcaseValidateRequest(BaseModel):
    brute_code: str = Field(..., min_length=1, description="Brute force reference solution")
    optimal_code: str = Field(..., min_length=1, description="Optimal reference solution")
    testcases: list[TestCase] = Field(..., min_length=1, description="Candidate test cases to validate")


class TestcaseValidateResponse(BaseModel):
    valid_testcases: list[TestCase]
    failed_testcases: list[dict]
    valid_count: int
    failed_count: int
    all_valid: bool
