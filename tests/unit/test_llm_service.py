import unittest
from unittest.mock import MagicMock
from app.services.llm_service import LLMService, LLMServiceError


class TestLLMService(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.service = LLMService(client=self.mock_client)

    def test_extract_solutions_success(self):
        raw = """
# BRUTE FORCE SOLUTION
def bruteforce_solve(n):
    return n * 2

# OPTIMAL SOLUTION
def optimal_solve(n):
    return n << 1
"""
        extracted = self.service.extract_solutions(raw)
        self.assertEqual(extracted.brute_code, "def bruteforce_solve(n):\n    return n * 2")
        self.assertEqual(extracted.optimal_code, "def optimal_solve(n):\n    return n << 1")

    def test_extract_solutions_markdown_wrapped(self):
        raw = """```python
# BRUTE FORCE SOLUTION
def bruteforce_solve(x): return x

# OPTIMAL SOLUTION
def optimal_solve(x): return x
```"""
        extracted = self.service.extract_solutions(raw)
        self.assertFalse(extracted.brute_code.startswith("```"))
        self.assertFalse(extracted.optimal_code.endswith("```"))

    def test_extract_solutions_missing_marker(self):
        raw = "def solve(): return 42"
        with self.assertRaises(LLMServiceError):
            self.service.extract_solutions(raw)

    def test_generate_reference_solutions_mocked(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="# BRUTE FORCE SOLUTION\ndef bruteforce_solve(): pass\n# OPTIMAL SOLUTION\ndef optimal_solve(): pass"
                )
            )
        ]
        self.mock_client.chat.completions.create.return_value = mock_response

        res = self.service.generate_reference_solutions("problem text")
        self.assertIn("bruteforce_solve", res.brute_code)
        self.assertIn("optimal_solve", res.optimal_code)

    def test_generate_reference_solutions_invalid_problem(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="INVALID_PROBLEM"))]
        self.mock_client.chat.completions.create.return_value = mock_response

        with self.assertRaises(LLMServiceError):
            self.service.generate_reference_solutions("gibberish")

    def test_generate_testcases_mocked(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"testcases": [{"input": 1, "expected_output": 2}, {"input": 2, "expected_output": 4}]}'
                )
            )
        ]
        self.mock_client.chat.completions.create.return_value = mock_response

        testcases = self.service.generate_testcases("Double problem")
        self.assertEqual(len(testcases), 2)
        self.assertEqual(testcases[0].input, 1)
        self.assertEqual(testcases[0].expected_output, 2)

    def test_generate_suggestion_mocked(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"mistake_type": "indexing", "issue": "0-based vs 1-based indexing", "hint": "Subtract 1"}'
                )
            )
        ]
        self.mock_client.chat.completions.create.return_value = mock_response

        suggestion = self.service.generate_suggestion(
            problem="sample",
            user_code="solve()",
            eval_result={"verdict": "Wrong Answer"},
        )
        self.assertEqual(suggestion.mistake_type, "indexing")
        self.assertEqual(suggestion.issue, "0-based vs 1-based indexing")
        self.assertEqual(suggestion.hint, "Subtract 1")


if __name__ == "__main__":
    unittest.main()
