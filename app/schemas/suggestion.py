from typing import Any, Optional
from pydantic import BaseModel, Field


class SuggestionRequest(BaseModel):
    problem: str = Field(..., min_length=3, description="Problem description")
    user_code: str = Field(..., min_length=1, description="Submitted user code")
    eval_result: dict[str, Any] = Field(..., description="Evaluation summary or result dictionary")
    model: Optional[str] = Field(default=None, description="Groq model override")


class SuggestionResponse(BaseModel):
    mistake_type: str = Field(..., description="Category of error (e.g., logic, syntax, boundary)")
    issue: str = Field(..., description="Clear explanation of the detected problem")
    hint: str = Field(..., description="Constructive guidance without full code disclosure")
    model_used: Optional[str] = None
