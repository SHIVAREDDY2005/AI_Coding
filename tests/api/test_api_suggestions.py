import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.api.deps import get_llm_service
from app.main import app
from app.schemas.suggestion import SuggestionResponse
from app.services.llm_service import LLMService, LLMServiceError


class TestApiSuggestions(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=LLMService)
        app.dependency_overrides[get_llm_service] = lambda: self.mock_llm
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_generate_suggestion_success(self):
        self.mock_llm.generate_suggestion.return_value = SuggestionResponse(
            mistake_type="logic_error",
            issue="Subtraction instead of addition",
            hint="Check arithmetic operator",
            model_used="test-model",
        )

        payload = {
            "problem": "Add two numbers",
            "user_code": "def solve(a, b): return a - b",
            "eval_result": {"verdict": "Wrong Answer"},
        }
        res = self.client.post("/api/v1/suggestions/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mistake_type"], "logic_error")
        self.assertEqual(data["issue"], "Subtraction instead of addition")
        self.assertEqual(data["hint"], "Check arithmetic operator")


if __name__ == "__main__":
    unittest.main()
