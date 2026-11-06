import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.api.deps import get_judge_service, get_llm_service, get_validation_service
from app.main import app
from app.schemas.judge import (
    JudgeExecutionResponse,
    JudgeSummary,
    JudgeTestCaseResult,
)
from app.schemas.solution import ExtractedSolutions
from app.schemas.suggestion import SuggestionResponse
from app.schemas.testcase import TestCase, TestcaseValidateResponse
from app.services.judge_service import JudgeService
from app.services.llm_service import LLMService
from app.services.validation_service import ValidationService


class TestApiPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=LLMService)
        self.mock_val = MagicMock(spec=ValidationService)
        self.mock_judge = MagicMock(spec=JudgeService)

        app.dependency_overrides[get_llm_service] = lambda: self.mock_llm
        app.dependency_overrides[get_validation_service] = lambda: self.mock_val
        app.dependency_overrides[get_judge_service] = lambda: self.mock_judge
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_run_pipeline_all_passed(self):
        # 1. Solutions
        self.mock_llm.generate_reference_solutions.return_value = ExtractedSolutions(
            brute_code="def bruteforce_solve(x): return x * 2",
            optimal_code="def optimal_solve(x): return x << 1",
        )
        # 2. Testcases
        testcase = TestCase(input=5, expected_output=10)
        self.mock_llm.generate_testcases.return_value = [testcase]

        # 3. Validation
        self.mock_val.validate_reference_solutions.return_value = TestcaseValidateResponse(
            valid_testcases=[testcase],
            failed_testcases=[],
            valid_count=1,
            failed_count=0,
            all_valid=True,
        )

        # 4. Evaluation
        self.mock_judge.evaluate_code.return_value = JudgeExecutionResponse(
            summary=JudgeSummary(passed=1, total=1, ran=1, verdict="All Passed"),
            results=[
                JudgeTestCaseResult(testcase=1, status="Accepted", passed=True, actual=10)
            ],
            detected_function="solve",
            language_id=71,
        )

        payload = {
            "problem": "Double the number",
            "user_code": "def solve(x): return x * 2",
            "language": "Python 3",
        }
        res = self.client.post("/api/v1/pipeline/run", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["testcases_validated"], 1)
        self.assertEqual(data["evaluation"]["summary"]["verdict"], "All Passed")
        self.assertIsNone(data["suggestion"])

    def test_run_pipeline_wrong_answer_includes_suggestion(self):
        # 1. Solutions
        self.mock_llm.generate_reference_solutions.return_value = ExtractedSolutions(
            brute_code="def bruteforce_solve(x): return x * 2",
            optimal_code="def optimal_solve(x): return x << 1",
        )
        # 2. Testcases
        testcase = TestCase(input=5, expected_output=10)
        self.mock_llm.generate_testcases.return_value = [testcase]

        # 3. Validation
        self.mock_val.validate_reference_solutions.return_value = TestcaseValidateResponse(
            valid_testcases=[testcase],
            failed_testcases=[],
            valid_count=1,
            failed_count=0,
            all_valid=True,
        )

        # 4. Evaluation (Wrong answer)
        self.mock_judge.evaluate_code.return_value = JudgeExecutionResponse(
            summary=JudgeSummary(passed=0, total=1, ran=1, verdict="Wrong Answer"),
            results=[
                JudgeTestCaseResult(testcase=1, status="Wrong Answer", passed=False, actual=5)
            ],
            detected_function="solve",
            language_id=71,
        )

        # 5. Suggestion
        self.mock_llm.generate_suggestion.return_value = SuggestionResponse(
            mistake_type="logic_error",
            issue="Returns input instead of doubling",
            hint="Multiply by 2",
        )

        payload = {
            "problem": "Double the number",
            "user_code": "def solve(x): return x",
            "language": "Python 3",
        }
        res = self.client.post("/api/v1/pipeline/run", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["success"])
        self.assertIsNotNone(data["suggestion"])
        self.assertEqual(data["suggestion"]["mistake_type"], "logic_error")
        self.assertEqual(data["suggestion"]["hint"], "Multiply by 2")


if __name__ == "__main__":
    unittest.main()
