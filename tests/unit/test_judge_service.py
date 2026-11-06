import unittest
from unittest.mock import patch, MagicMock
from app.schemas.testcase import TestCase
from app.services.judge_service import JudgeService, JudgeServiceError


class TestJudgeService(unittest.TestCase):
    def setUp(self):
        self.service = JudgeService()

    @patch("requests.post")
    def test_evaluate_code_all_passed(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "42\n",
            "time": "0.01",
            "memory": "1024",
        }
        mock_post.return_value = mock_resp

        code = "def solve(x): return x * 2"
        testcases = [TestCase(input={"x": 21}, expected_output=42)]

        res = self.service.evaluate_code(code, "Python 3", testcases)
        self.assertEqual(res.summary.verdict, "All Passed")
        self.assertEqual(res.summary.passed, 1)
        self.assertEqual(res.summary.total, 1)
        self.assertEqual(len(res.results), 1)
        self.assertTrue(res.results[0].passed)
        self.assertEqual(res.detected_function, "solve")

    @patch("requests.post")
    def test_evaluate_code_wrong_answer(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "40\n",
        }
        mock_post.return_value = mock_resp

        code = "def solve(x): return x"
        testcases = [TestCase(input={"x": 21}, expected_output=42)]

        res = self.service.evaluate_code(code, 71, testcases)
        self.assertEqual(res.summary.verdict, "Wrong Answer")
        self.assertEqual(res.summary.passed, 0)
        self.assertFalse(res.results[0].passed)

    @patch("requests.post")
    def test_evaluate_code_compilation_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": {"description": "Compilation Error"},
            "compile_output": "SyntaxError: unexpected EOF",
        }
        mock_post.return_value = mock_resp

        code = "def broken():"
        testcases = [TestCase(input=1, expected_output=1)]

        res = self.service.evaluate_code(code, "python", testcases)
        self.assertEqual(res.summary.verdict, "Compilation Error")
        self.assertEqual(res.summary.passed, 0)
        self.assertIn("SyntaxError", res.results[0].error)

    @patch("requests.post")
    def test_evaluate_code_runtime_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": {"description": "Runtime Error (NZEC)"},
            "stderr": "ZeroDivisionError: division by zero",
        }
        mock_post.return_value = mock_resp

        code = "def solve(x): return 1 / 0"
        testcases = [TestCase(input=1, expected_output=1)]

        res = self.service.evaluate_code(code, "python", testcases)
        self.assertEqual(res.summary.verdict, "Runtime Error (NZEC)")
        self.assertEqual(res.summary.passed, 0)
        self.assertIn("ZeroDivisionError", res.results[0].error)

    @patch("requests.post")
    def test_judge0_unreachable_raises_judge_service_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.RequestException("Host unreachable")

        code = "def solve(): return 1"
        testcases = [TestCase(input=1, expected_output=1)]

        with self.assertRaises(JudgeServiceError):
            self.service.evaluate_code(code, "python", testcases)


if __name__ == "__main__":
    unittest.main()
