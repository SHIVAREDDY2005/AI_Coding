import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.api.deps import get_judge_service
from app.main import app
from app.schemas.judge import (
    JudgeExecutionResponse,
    JudgeSummary,
    JudgeTestCaseResult,
)
from app.services.judge_service import JudgeService, JudgeServiceError


class TestApiJudge(unittest.TestCase):
    def setUp(self):
        self.mock_judge = MagicMock(spec=JudgeService)
        app.dependency_overrides[get_judge_service] = lambda: self.mock_judge
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_evaluate_code_success(self):
        self.mock_judge.evaluate_code.return_value = JudgeExecutionResponse(
            summary=JudgeSummary(passed=1, total=1, ran=1, verdict="All Passed"),
            results=[
                JudgeTestCaseResult(testcase=1, status="Accepted", passed=True, actual=42)
            ],
            detected_function="solve",
            language_id=71,
        )

        payload = {
            "code": "def solve(x): return x * 2",
            "language": "Python 3",
            "testcases": [{"input": 21, "expected_output": 42}],
        }
        res = self.client.post("/api/v1/judge/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["summary"]["verdict"], "All Passed")
        self.assertEqual(data["detected_function"], "solve")

    def test_evaluate_code_invalid_language(self):
        self.mock_judge.evaluate_code.side_effect = ValueError("Unsupported language: xyz")

        payload = {
            "code": "print(1)",
            "language": "xyz",
            "testcases": [{"input": 1, "expected_output": 1}],
        }
        res = self.client.post("/api/v1/judge/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported language", res.json()["detail"])

    def test_evaluate_code_judge_unreachable(self):
        self.mock_judge.evaluate_code.side_effect = JudgeServiceError("Judge0 unreachable")

        payload = {
            "code": "print(1)",
            "language": "Python 3",
            "testcases": [{"input": 1, "expected_output": 1}],
        }
        res = self.client.post("/api/v1/judge/evaluate", json=payload)
        self.assertEqual(res.status_code, 502)
        self.assertIn("Judge0 unreachable", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
