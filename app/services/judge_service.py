import json
from typing import Any, Callable, Optional, Union
import requests

from app.core.config import Settings, get_settings
from app.core.languages import resolve_language_id
from app.schemas.judge import (
    JudgeExecutionResponse,
    JudgeSummary,
    JudgeTestCaseResult,
)
from app.schemas.testcase import TestCase
from app.services.harness_service import HarnessService


class JudgeServiceError(Exception):
    """Raised when communication with Judge0 fails."""
    pass


class JudgeService:
    """
    Service responsible for interacting with Judge0 to execute
    code in an isolated sandbox.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        harness_service: Optional[HarnessService] = None,
        submit_fn: Optional[Callable[[str, int, str], dict]] = None,
    ):
        self.settings = settings or get_settings()
        self.harness_service = harness_service or HarnessService()
        self._headers = {"Content-Type": "application/json"}
        self._submit_fn = submit_fn

    def submit_raw(self, source_code: str, language_id: int, stdin: str) -> dict:
        """
        Submits code directly to Judge0.
        Raises JudgeServiceError if Judge0 is unreachable.
        """
        if self._submit_fn is not None:
            return self._submit_fn(source_code, language_id, stdin)

        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "stdin": stdin,
        }
        try:
            res = requests.post(
                self.settings.JUDGE0_URL,
                headers=self._headers,
                json=payload,
                timeout=self.settings.JUDGE0_TIMEOUT,
            )
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            raise JudgeServiceError(f"Judge0 execution failed or unreachable: {str(e)}") from e

    def evaluate_code(
        self,
        code: str,
        language: Union[int, str],
        testcases: list[TestCase],
    ) -> JudgeExecutionResponse:
        """
        Wraps user code into a language harness and evaluates it
        against all provided test cases.
        """
        if not testcases:
            raise ValueError("At least one testcase is required for evaluation")

        language_id = resolve_language_id(language)
        if not self.harness_service.is_language_supported(language_id):
            raise ValueError(f"Language ID {language_id} is not supported by execution harness")

        sample_input = testcases[0].input
        fn_name = self.harness_service.detect_function_name(code, language_id)
        harness_code = self.harness_service.build_harness(
            code=code,
            language_id=language_id,
            sample_input=sample_input,
            function_name=fn_name,
        )

        results: list[JudgeTestCaseResult] = []
        passed = 0

        for i, tc in enumerate(testcases, start=1):
            stdin_payload = json.dumps(tc.input)
            data = self.submit_raw(harness_code, language_id, stdin_payload)

            status = data.get("status", {}).get("description", "Unknown")

            # Compilation Error → stop immediately
            if status == "Compilation Error":
                results.append(
                    JudgeTestCaseResult(
                        testcase=i,
                        status="Compilation Error",
                        passed=False,
                        error=data.get("compile_output", "").strip(),
                    )
                )
                break

            # Runtime Error → stop immediately
            if "Runtime Error" in status:
                results.append(
                    JudgeTestCaseResult(
                        testcase=i,
                        status=status,
                        passed=False,
                        input=tc.input,
                        error=(data.get("stderr") or "").strip(),
                    )
                )
                break

            # TLE → stop immediately
            if status == "Time Limit Exceeded":
                results.append(
                    JudgeTestCaseResult(
                        testcase=i,
                        status="Time Limit Exceeded",
                        passed=False,
                        input=tc.input,
                    )
                )
                break

            # Other non-accepted status
            if status != "Accepted":
                results.append(
                    JudgeTestCaseResult(
                        testcase=i,
                        status=status,
                        passed=False,
                        error=(data.get("stderr") or data.get("compile_output") or "").strip(),
                    )
                )
                break

            # Parse stdout JSON
            raw_stdout = data.get("stdout") or ""
            try:
                actual = json.loads(raw_stdout.strip())
            except Exception as e:
                results.append(
                    JudgeTestCaseResult(
                        testcase=i,
                        status="Output Parse Error",
                        passed=False,
                        raw=raw_stdout.strip(),
                        error=str(e),
                    )
                )
                break

            is_correct = (actual == tc.expected_output)
            if is_correct:
                passed += 1

            results.append(
                JudgeTestCaseResult(
                    testcase=i,
                    status="Accepted" if is_correct else "Wrong Answer",
                    passed=is_correct,
                    input=tc.input,
                    expected=tc.expected_output,
                    actual=actual,
                    time=data.get("time"),
                    memory=data.get("memory"),
                )
            )

            if not is_correct:
                break

        total = len(testcases)
        verdict = "All Passed" if passed == total else (results[-1].status if results else "No Tests")

        return JudgeExecutionResponse(
            summary=JudgeSummary(
                passed=passed,
                total=total,
                ran=len(results),
                verdict=verdict,
            ),
            results=results,
            detected_function=fn_name,
            language_id=language_id,
        )
