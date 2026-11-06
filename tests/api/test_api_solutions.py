import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.api.deps import get_llm_service
from app.main import app
from app.schemas.solution import ExtractedSolutions
from app.services.llm_service import LLMService, LLMServiceError


class TestApiSolutions(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=LLMService)
        app.dependency_overrides[get_llm_service] = lambda: self.mock_llm
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_generate_solutions_success(self):
        self.mock_llm.generate_reference_solutions.return_value = ExtractedSolutions(
            brute_code="def bruteforce_solve(): pass",
            optimal_code="def optimal_solve(): pass",
        )

        payload = {"problem": "Given an array, find the sum"}
        res = self.client.post("/api/v1/solutions/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["brute_code"], "def bruteforce_solve(): pass")
        self.assertEqual(data["optimal_code"], "def optimal_solve(): pass")

    def test_generate_solutions_error(self):
        self.mock_llm.generate_reference_solutions.side_effect = LLMServiceError("Model error")

        payload = {"problem": "Short problem"}
        res = self.client.post("/api/v1/solutions/generate", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Model error", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
