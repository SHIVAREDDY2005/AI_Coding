import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.api.deps import get_llm_service, get_validation_service
from app.main import app
from app.schemas.testcase import TestCase, TestcaseValidateResponse
from app.services.llm_service import LLMService, LLMServiceError
from app.services.validation_service import ValidationService


class TestApiTestcases(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=LLMService)
        self.mock_val = MagicMock(spec=ValidationService)
        app.dependency_overrides[get_llm_service] = lambda: self.mock_llm
        app.dependency_overrides[get_validation_service] = lambda: self.mock_val
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_generate_testcases_success(self):
        self.mock_llm.generate_testcases.return_value = [
            TestCase(input=1, expected_output=2),
            TestCase(input=2, expected_output=4),
        ]

        payload = {"problem": "Double the number"}
        res = self.client.post("/api/v1/testcases/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["testcases"]), 2)

    def test_generate_testcases_error(self):
        self.mock_llm.generate_testcases.side_effect = LLMServiceError("Invalid problem")

        payload = {"problem": "Bad problem"}
        res = self.client.post("/api/v1/testcases/generate", json=payload)
        self.assertEqual(res.status_code, 400)

    def test_validate_testcases_success(self):
        self.mock_val.validate_reference_solutions.return_value = TestcaseValidateResponse(
            valid_testcases=[TestCase(input=1, expected_output=2)],
            failed_testcases=[],
            valid_count=1,
            failed_count=0,
            all_valid=True,
        )

        payload = {
            "brute_code": "def bruteforce_solve(x): return x * 2",
            "optimal_code": "def optimal_solve(x): return x * 2",
            "testcases": [{"input": 1, "expected_output": 2}],
        }
        res = self.client.post("/api/v1/testcases/validate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["all_valid"])
        self.assertEqual(data["valid_count"], 1)


if __name__ == "__main__":
    unittest.main()
