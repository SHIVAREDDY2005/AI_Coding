from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="2.0.0", description="Application version")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message description")
