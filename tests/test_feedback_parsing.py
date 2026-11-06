import unittest
from unittest.mock import MagicMock
from funtions.suggestion import parse_suggestion_json, generate_suggestion


class TestFeedbackParsing(unittest.TestCase):
    def test_parse_suggestion_json_clean(self):
        content = '{"mistake_type": "off_by_one", "issue": "Loop boundary issue", "hint": "Check upper bound"}'
        res = parse_suggestion_json(content)
        self.assertEqual(res["mistake_type"], "off_by_one")
        self.assertEqual(res["issue"], "Loop boundary issue")
        self.assertEqual(res["hint"], "Check upper bound")

    def test_parse_suggestion_json_markdown_wrapped(self):
        content = """```json
{
  "mistake_type": "type_error",
  "issue": "Cannot add string to int",
  "hint": "Convert string to int using int()"
}
```"""
        res = parse_suggestion_json(content)
        self.assertEqual(res["mistake_type"], "type_error")
        self.assertIn("int()", res["hint"])

    def test_parse_suggestion_json_fallback(self):
        content = "This is not json at all."
        res = parse_suggestion_json(content)
        self.assertEqual(res["mistake_type"], "unknown")
        self.assertEqual(res["issue"], content)

    def test_generate_suggestion_mocked(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"mistake_type": "logic", "issue": "Minus instead of plus", "hint": "Use +" }'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        res = generate_suggestion(
            client=mock_client,
            problem="Add 2 numbers",
            usercode="def add(a, b): return a - b",
            result={"verdict": "Wrong Answer"},
            model="mock-model"
        )

        self.assertEqual(res["mistake_type"], "logic")
        self.assertEqual(res["issue"], "Minus instead of plus")
        self.assertEqual(res["hint"], "Use +")


if __name__ == "__main__":
    unittest.main()
