import unittest
from unittest.mock import patch, MagicMock
from funtions.complete_test_cases.testcase_validation_Judge0 import encode, decode, run_code


class TestJudge0Parsing(unittest.TestCase):
    def test_encode_decode(self):
        original = "print('hello world')"
        encoded = encode(original)
        self.assertNotEqual(original, encoded)
        decoded = decode(encoded)
        self.assertEqual(original, decoded)

    def test_decode_empty_or_none(self):
        self.assertEqual(decode(""), "")
        self.assertEqual(decode(None), "")

    def test_decode_invalid_base64_fallback(self):
        raw = "not_valid_b64"
        self.assertEqual(decode(raw), raw)

    @patch("requests.post")
    def test_run_code_accepted(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "stdout": encode("12\n"),
            "stderr": None,
            "compile_output": None,
            "status": {"description": "Accepted"},
            "time": "0.02",
            "memory": "1024"
        }
        mock_post.return_value = mock_resp

        res = run_code(
            language_id=71,
            code="a, b = map(int, input().split()); print(a + b)",
            test_cases=[{"input": "5 7", "expected": "12"}]
        )

        self.assertTrue(res["valid"])
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["results"][0]["status"], "Accepted")

    @patch("requests.post")
    def test_run_code_wrong_answer(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "stdout": encode("10\n"),
            "stderr": None,
            "compile_output": None,
            "status": {"description": "Accepted"},
        }
        mock_post.return_value = mock_resp

        res = run_code(
            language_id=71,
            code="dummy",
            test_cases=[{"input": "5 7", "expected": "12"}]
        )

        self.assertFalse(res["valid"])
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["results"][0]["output"], "10")


if __name__ == "__main__":
    unittest.main()
