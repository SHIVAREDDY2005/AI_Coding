import json
from typing import Optional

from app.schemas.testcase import TestCase, TestcaseValidateResponse
from app.services.harness_service import HarnessService
from app.services.judge_service import JudgeService


class ValidationService:
    """
    Coordinates reference-solution verification using Judge0.
    Ensures zero un-sandboxed code runs on the host application.
    """

    def __init__(
        self,
        judge_service: Optional[JudgeService] = None,
        harness_service: Optional[HarnessService] = None,
    ):
        self.harness_service = harness_service or HarnessService()
        self.judge_service = judge_service or JudgeService(harness_service=self.harness_service)

    def validate_reference_solutions(
        self,
        brute_code: str,
        optimal_code: str,
        testcases: list[TestCase],
    ) -> TestcaseValidateResponse:
        """
        Runs candidate test cases against both brute and optimal solutions in Judge0.
        Only test cases where both solutions produce the expected output are marked valid.
        """
        if not testcases:
            return TestcaseValidateResponse(
                valid_testcases=[],
                failed_testcases=[],
                valid_count=0,
                failed_count=0,
                all_valid=False,
            )

        brute_fn = self.harness_service.detect_function_name(brute_code, 71) or "bruteforce_solve"
        opt_fn = self.harness_service.detect_function_name(optimal_code, 71) or "optimal_solve"

        valid_cases: list[TestCase] = []
        failed_cases: list[dict] = []

        for i, tc in enumerate(testcases, start=1):
            try:
                sample_input = tc.input
                stdin_payload = json.dumps(sample_input)

                brute_wrapped = self.harness_service.build_harness(
                    code=brute_code,
                    language_id=71,
                    sample_input=sample_input,
                    function_name=brute_fn,
                )
                opt_wrapped = self.harness_service.build_harness(
                    code=optimal_code,
                    language_id=71,
                    sample_input=sample_input,
                    function_name=opt_fn,
                )

                # Execute brute force on Judge0
                brute_res = self.judge_service.submit_raw(brute_wrapped, 71, stdin_payload)
                brute_status = brute_res.get("status", {}).get("description", "Unknown")

                if brute_status != "Accepted":
                    failed_cases.append({
                        "testcase": i,
                        "input": tc.input,
                        "reason": f"Brute solution failed: {brute_status}",
                        "error": brute_res.get("stderr") or brute_res.get("compile_output"),
                    })
                    continue

                # Execute optimal on Judge0
                opt_res = self.judge_service.submit_raw(opt_wrapped, 71, stdin_payload)
                opt_status = opt_res.get("status", {}).get("description", "Unknown")

                if opt_status != "Accepted":
                    failed_cases.append({
                        "testcase": i,
                        "input": tc.input,
                        "reason": f"Optimal solution failed: {opt_status}",
                        "error": opt_res.get("stderr") or opt_res.get("compile_output"),
                    })
                    continue

                # Parse JSON outputs
                brute_out = json.loads(brute_res.get("stdout", "").strip())
                opt_out = json.loads(opt_res.get("stdout", "").strip())

                if brute_out == tc.expected_output and opt_out == tc.expected_output:
                    valid_cases.append(tc)
                else:
                    failed_cases.append({
                        "testcase": i,
                        "input": tc.input,
                        "expected": tc.expected_output,
                        "brute_output": brute_out,
                        "optimal_output": opt_out,
                        "reason": "Output mismatch against expected output",
                    })

            except Exception as e:
                failed_cases.append({
                    "testcase": i,
                    "input": tc.input,
                    "error": str(e),
                    "reason": "Exception during sandboxed validation",
                })

        return TestcaseValidateResponse(
            valid_testcases=valid_cases,
            failed_testcases=failed_cases,
            valid_count=len(valid_cases),
            failed_count=len(failed_cases),
            all_valid=len(failed_cases) == 0 and len(valid_cases) > 0,
        )
