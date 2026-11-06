"""
Backwards-compatibility adapter for usercode_evaluation.
Delegates to app.services.judge_service and app.main.
"""
import requests
from typing import Any, Union
from fastapi import HTTPException
from app.core.config import get_settings
from app.core.languages import resolve_language_id, get_supported_languages
from app.main import app
from app.schemas.judge import JudgeExecutionRequest as JudgeRequest
from app.schemas.testcase import TestCase
from app.services.harness_service import HarnessService, PythonHarness
from app.services.judge_service import JudgeService, JudgeServiceError

_settings = get_settings()
JUDGE0_URL = _settings.JUDGE0_URL
JUDGE0_HEADERS = {"Content-Type": "application/json"}

_harness = HarnessService()


def _submit_to_judge0_real(source_code: str, language_id: int, stdin: str, url: str = None, headers: dict = None) -> dict:
    payload = {
        "language_id": language_id,
        "source_code": source_code,
        "stdin": stdin,
    }
    try:
        res = requests.post(
            url or _settings.JUDGE0_URL,
            headers=headers or JUDGE0_HEADERS,
            json=payload,
            timeout=_settings.JUDGE0_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Judge0 unreachable: {str(e)}") from e


def submit_to_judge0(source_code: str, language_id: int, stdin: str, url: str = None, headers: dict = None) -> dict:
    return _submit_to_judge0_real(source_code, language_id, stdin, url=url, headers=headers)


def detect_func_name(code: str, language_id: int) -> str:
    return _harness.detect_function_name(code, language_id)


def evaluate_user_code(
    code: str,
    testcases: list,
    language: Union[int, str],
    judge0_url: str = None,
    judge0_headers: dict = None
) -> dict:
    parsed_cases = []
    for tc in testcases:
        if isinstance(tc, TestCase):
            parsed_cases.append(tc)
        elif isinstance(tc, dict):
            inp = tc.get("input")
            exp = tc.get("expected_output", tc.get("expected"))
            parsed_cases.append(TestCase(input=inp, expected_output=exp))
        elif hasattr(tc, "input") and hasattr(tc, "expected_output"):
            parsed_cases.append(TestCase(input=tc.input, expected_output=tc.expected_output))

    # Connect to submit_to_judge0 in module scope so test mocks can intercept
    judge_instance = JudgeService(
        settings=_settings,
        harness_service=_harness,
        submit_fn=lambda s, l, i: submit_to_judge0(s, l, i, url=judge0_url, headers=judge0_headers)
    )

    res = judge_instance.evaluate_code(code=code, language=language, testcases=parsed_cases)
    return res.model_dump()


usercode_evaluation = evaluate_user_code

__all__ = [
    "app",
    "JUDGE0_URL",
    "JUDGE0_HEADERS",
    "TestCase",
    "JudgeRequest",
    "PythonHarness",
    "resolve_language_id",
    "detect_func_name",
    "submit_to_judge0",
    "evaluate_user_code",
    "usercode_evaluation",
]
