import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Coding Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # LLM Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY_1: str = ""

    # Judge0 Settings
    JUDGE0_URL: str = "https://ce.judge0.com/submissions?wait=true"
    JUDGE0_URL_BASE64: str = "https://ce.judge0.com/submissions?wait=true&base64_encoded=true"
    JUDGE0_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
