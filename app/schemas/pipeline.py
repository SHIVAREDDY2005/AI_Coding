from typing import Optional, Union
from pydantic import BaseModel, Field
from app.schemas.judge import JudgeExecutionResponse
from app.schemas.solution import ExtractedSolutions
from app.schemas.suggestion import SuggestionResponse


class PipelineRunRequest(BaseModel):
    problem: str = Field(..., min_length=5, description="Problem description")
    user_code: str = Field(..., min_length=1, description="User submitted source code")
    language: Union[int, str] = Field(default="Python 3", description="Language name or ID")
    model: Optional[str] = Field(default=None, description="Groq model override")


class PipelineRunResponse(BaseModel):
    problem: str
    solutions: Optional[ExtractedSolutions] = None
    testcases_generated: int = 0
    testcases_validated: int = 0
    evaluation: Optional[JudgeExecutionResponse] = None
    suggestion: Optional[SuggestionResponse] = None
    success: bool = False
    message: str = ""
