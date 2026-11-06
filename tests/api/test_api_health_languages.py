import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestApiHealthAndLanguages(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("docs", data)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_api_v1_health(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_languages_endpoint(self):
        res = self.client.get("/api/v1/languages")
        self.assertEqual(res.status_code, 200)
        langs = res.json()["languages"]
        self.assertTrue(len(langs) >= 8)
        names = [l["name"] for l in langs]
        self.assertIn("Python 3", names)
        self.assertIn("C++ 17", names)
        self.assertIn("JavaScript (Node.js)", names)


if __name__ == "__main__":
    unittest.main()
