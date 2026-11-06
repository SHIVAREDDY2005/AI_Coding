import unittest
from unittest.mock import MagicMock
from funtions.complete_test_cases.generate_testcases import safe_json_parse, generate_testcases


class TestTestCaseGenerationAndParsing(unittest.TestCase):
    def test_safe_json_parse_clean(self):
        raw = '{"testcases": [{"input": 12, "expected_output": 21}]}'
        parsed = safe_json_parse(raw)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(len(parsed["testcases"]), 1)
        self.assertEqual(parsed["testcases"][0]["input"], 12)

    def test_safe_json_parse_markdown_fenced(self):
        raw = """```json
{
  "testcases": [
    {"input": {"nums": [1, 2]}, "expected_output": 3}
  ]
}
```"""
        parsed = safe_json_parse(raw)
        self.assertIsInstance(parsed, dict)
        self.assertIn("testcases", parsed)
        self.assertEqual(parsed["testcases"][0]["expected_output"], 3)

    def test_safe_json_parse_invalid(self):
        raw = "Not a json response"
        parsed = safe_json_parse(raw)
        self.assertIsNone(parsed)

    def test_generate_testcases_mocked_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"testcases": [{"input": 5, "expected_output": 10}]}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        res = generate_testcases(mock_client, "Double a number", model="mock-model")
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["input"], 5)
        self.assertEqual(res[0]["expected_output"], 10)

    def test_generate_testcases_mocked_validation_error(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"error": "Invalid problem description"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        res = generate_testcases(mock_client, "Gibberish problem", model="mock-model")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
