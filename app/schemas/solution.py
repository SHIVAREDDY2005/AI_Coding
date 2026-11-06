from typing import Optional
from pydantic import BaseModel, Field


class SolutionGenerateRequest(BaseModel):
    problem: str = Field(..., min_length=5, description="Competitive programming problem statement")
    model: Optional[str] = Field(default=None, description="Groq model identifier")


class ExtractedSolutions(BaseModel):
    brute_code: str = Field(..., description="Brute force reference Python solution")
    optimal_code: str = Field(..., description="Optimal reference Python solution")


class SolutionGenerateResponse(BaseModel):
    brute_code: str
    optimal_code: str
    raw_output: Optional[str] = None
    model_used: str
