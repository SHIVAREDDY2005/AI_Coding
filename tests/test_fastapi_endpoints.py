import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from funtions.usercode_evaluation import app


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_languages_endpoint(self):
        response = self.client.get("/languages")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("languages", data)
        lang_names = [l["name"] for l in data["languages"]]
        self.assertIn("Python 3", lang_names)
        self.assertIn("C++ 17", lang_names)

    @patch("funtions.usercode_evaluation.submit_to_judge0")
    def test_judge_endpoint_success(self, mock_submit):
        mock_submit.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "15\n",
            "time": "0.01",
            "memory": "512"
        }

        payload = {
            "code": "def solve(a, b): return a + b",
            "testcases": [
                {"input": {"a": 5, "b": 10}, "expected_output": 15}
            ],
            "language_id": "Python 3"
        }

        response = self.client.post("/judge", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["summary"]["verdict"], "All Passed")
        self.assertEqual(body["summary"]["passed"], 1)

    def test_judge_endpoint_invalid_language(self):
        payload = {
            "code": "def solve(): pass",
            "testcases": [{"input": 1, "expected_output": 1}],
            "language_id": "unknown_lang_xyz"
        }
        response = self.client.post("/judge", json=payload)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
