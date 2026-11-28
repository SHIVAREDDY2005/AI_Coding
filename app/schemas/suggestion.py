from typing import Any, Optional
from pydantic import BaseModel, Field


class SuggestionRequest(BaseModel):
    problem: str = Field(..., min_length=3, description="Problem description")
    user_code: str = Field(..., min_length=1, description="Submitted user code")
    eval_result: dict[str, Any] = Field(..., description="Evaluation summary or result dictionary")
    language: Optional[str] = Field(default=None, description="Programming language of user_code")
    testcases: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Current workspace test cases (input / expected_output)"
    )
    feedback_focus: Optional[str] = Field(
        default=None,
        description="Requested feedback style or question (e.g. optimize, debug, edge_cases, or custom prompt)",
    )
    conversation_history: Optional[list[dict[str, str]]] = Field(
        default=None,
        description="Prior chat turns in this mentoring session",
    )
    model: Optional[str] = Field(default=None, description="Groq model override")


class SuggestionResponse(BaseModel):
    mistake_type: str = Field(..., description="Category of error or feedback (e.g., logic, syntax, optimization)")
    issue: str = Field(..., description="Clear explanation of the detected problem or current code behavior")
    hint: str = Field(..., description="Constructive guidance tailored to the user's request")
    complexity: Optional[str] = Field(default=None, description="Time and space complexity analysis")
    optimization: Optional[str] = Field(default=None, description="How to optimize the user's solution")
    model_used: Optional[str] = None
