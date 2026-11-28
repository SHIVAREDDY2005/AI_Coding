from typing import Optional
from pydantic import BaseModel, Field


class SimilarProblemRequest(BaseModel):
    problem: str = Field(..., min_length=5, description="DSA problem description")
    refresh: bool = Field(default=False, description="Bypass response cache")
    platform: Optional[str] = Field(
        default=None,
        description="Optional single platform to fetch/refresh (leetcode, codechef, or codeforces)",
    )
    solved_urls: list[str] = Field(default_factory=list, description="URLs of problems already solved by user")
    attempted_urls: list[str] = Field(default_factory=list, description="URLs of problems attempted by user")
    exclude_solved: bool = Field(default=False, description="Whether to exclude already-solved problems")
    target_difficulty: Optional[str] = Field(default=None, description="Optional target difficulty (easy, medium, hard)")
    model: Optional[str] = Field(default=None, description="Groq model override")


class SimilarProblemItem(BaseModel):
    title: str = Field(..., description="Problem title on the target platform")
    platform: str = Field(..., description="Platform name (leetcode, codechef, or codeforces)")
    url: str = Field(..., description="Direct URL to solve the problem on the target platform")
    similarity_score: int = Field(..., ge=0, le=100, description="Similarity score out of 100")
    difficulty: Optional[str] = Field(default=None, description="Problem difficulty or rating")
    tags: list[str] = Field(default_factory=list, description="Topic tags")
    reason: str = Field(..., description="Why this problem is similar")


class SimilarProblemsResponse(BaseModel):
    leetcode: list[SimilarProblemItem] = Field(default_factory=list)
    codechef: list[SimilarProblemItem] = Field(default_factory=list)
    codeforces: list[SimilarProblemItem] = Field(default_factory=list)
    platform_status: dict[str, str] = Field(
        default_factory=dict,
        description="Integration status per platform (e.g. live, imported dataset, rate_limited, unavailable)",
    )
    model_used: Optional[str] = None
