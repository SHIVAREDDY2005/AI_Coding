import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import requests
from funtions.usercode_evaluation import evaluate_user_code, submit_to_judge0
from funtions.complete_test_cases.write_code import write_code
from funtions.complete_test_cases.generate_testcases import generate_testcases


class TestFailureScenarios(unittest.TestCase):
    def test_evaluate_user_code_empty_testcases(self):
        with self.assertRaises(ValueError):
            evaluate_user_code("def solve(): pass", [], "python")

    def test_evaluate_user_code_unsupported_language(self):
        with self.assertRaises(ValueError):
            evaluate_user_code("def solve(): pass", [{"input": 1, "expected_output": 1}], "brainfuck")

    @patch("requests.post")
    def test_submit_to_judge0_network_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("Connection refused")
        with self.assertRaises(HTTPException) as ctx:
            submit_to_judge0("print(1)", 71, "")
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("Judge0 unreachable", ctx.exception.detail)

    def test_write_code_api_error_handling(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
        res = write_code(mock_client, "Sample problem", "mock-model")
        self.assertIsNone(res)

    def test_generate_testcases_api_error_handling(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Timeout")
        res = generate_testcases(mock_client, "Sample problem", "mock-model")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
