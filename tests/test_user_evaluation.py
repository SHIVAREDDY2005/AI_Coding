import unittest
from unittest.mock import patch
from funtions.usercode_evaluation import evaluate_user_code, TestCase


class TestUserEvaluation(unittest.TestCase):
    @patch("funtions.usercode_evaluation.submit_to_judge0")
    def test_evaluate_user_code_all_passed(self, mock_submit):
        mock_submit.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "42\n",
            "time": "0.01",
            "memory": "512"
        }

        user_code = "def solve(x): return x * 2"
        testcases = [
            {"input": {"x": 21}, "expected_output": 42}
        ]

        result = evaluate_user_code(user_code, testcases, "Python 3")
        self.assertEqual(result["summary"]["verdict"], "All Passed")
        self.assertEqual(result["summary"]["passed"], 1)
        self.assertEqual(result["summary"]["total"], 1)
        self.assertEqual(result["detected_function"], "solve")

    @patch("funtions.usercode_evaluation.submit_to_judge0")
    def test_evaluate_user_code_wrong_answer(self, mock_submit):
        mock_submit.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "40\n",
            "time": "0.01",
            "memory": "512"
        }

        user_code = "def solve(x): return x"
        testcases = [
            {"input": {"x": 21}, "expected_output": 42}
        ]

        result = evaluate_user_code(user_code, testcases, 71)
        self.assertEqual(result["summary"]["verdict"], "Wrong Answer")
        self.assertEqual(result["summary"]["passed"], 0)

    @patch("funtions.usercode_evaluation.submit_to_judge0")
    def test_evaluate_user_code_compilation_error(self, mock_submit):
        mock_submit.return_value = {
            "status": {"description": "Compilation Error"},
            "compile_output": "SyntaxError: invalid syntax",
        }

        user_code = "def broken():"
        testcases = [{"input": 1, "expected_output": 1}]

        result = evaluate_user_code(user_code, testcases, "python")
        self.assertEqual(result["summary"]["verdict"], "Compilation Error")
        self.assertEqual(result["summary"]["passed"], 0)
        self.assertIn("SyntaxError", result["results"][0]["error"])

    @patch("funtions.usercode_evaluation.submit_to_judge0")
    def test_evaluate_user_code_primitive_input(self, mock_submit):
        mock_submit.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "6\n",
        }

        user_code = "def factorial(n): return 6"
        testcases = [TestCase(input=3, expected_output=6)]

        result = evaluate_user_code(user_code, testcases, "python")
        self.assertEqual(result["summary"]["verdict"], "All Passed")


if __name__ == "__main__":
    unittest.main()
