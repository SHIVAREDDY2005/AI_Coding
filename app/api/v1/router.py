from fastapi import APIRouter
from app.api.v1.endpoints import health, judge, pipeline, solutions, suggestions, testcases

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Info"])
api_router.include_router(solutions.router, prefix="/solutions", tags=["Solutions"])
api_router.include_router(testcases.router, prefix="/testcases", tags=["Test Cases"])
api_router.include_router(judge.router, prefix="/judge", tags=["Judge & Execution"])
api_router.include_router(suggestions.router, prefix="/suggestions", tags=["Suggestions"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
