import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.services.embedding_service import EmbeddingService
from app.services.leetcode_catalog import (
    import_leetcode_csv,
    import_leetcode_json,
    load_leetcode_catalog,
)
from app.services.llm_service import LLMService
from app.services.similar_service import (
    SimilarProblemsService,
    clear_similar_caches,
    compute_similarity_score,
)


class TestSimilarProblemsService(unittest.TestCase):
    def setUp(self):
        clear_similar_caches()
        self.mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"tags": ["dp", "math"], "algorithms": ["knapsack", "divisibility"], "keywords": ["budget", "coin"]}'
                )
            )
        ]
        self.mock_client.chat.completions.create.return_value = mock_response
        self.llm = LLMService(client=self.mock_client)
        self.disabled_emb = EmbeddingService(enabled=False)

    def test_leetcode_json_and_csv_import_and_missing_catalog_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            missing_items, missing_status = load_leetcode_catalog(tmp_dir / "missing.json")
            self.assertEqual(missing_items, [])
            self.assertIn("unavailable", missing_status)

            src_json = tmp_dir / "src.json"
            src_json.write_text(
                '[{"task_id": "coin-change", "difficulty": "Medium", "tags": ["Dynamic Programming"], "problem_description": "Fewest coins to make amount."}]',
                encoding="utf-8",
            )
            dest_json = tmp_dir / "catalog.json"
            imported = import_leetcode_json(src_json, dest_json)
            self.assertEqual(len(imported), 1)
            self.assertEqual(imported[0].url, "https://leetcode.com/problems/coin-change/")

            src_csv = tmp_dir / "src.csv"
            src_csv.write_text(
                "slug,title,difficulty,tags,description\n"
                "two-sum,Two Sum,Easy,\"Array,Hash Table\",Find two numbers adding up to target\n",
                encoding="utf-8",
            )
            dest_csv_json = tmp_dir / "catalog_csv.json"
            imported_csv = import_leetcode_csv(src_csv, dest_csv_json)
            self.assertEqual(len(imported_csv), 1)
            self.assertEqual(imported_csv[0].title, "Two Sum")

            service = SimilarProblemsService(
                llm_service=self.llm,
                embedding_service=self.disabled_emb,
                leetcode_catalog_path=tmp_dir / "missing.json",
                fetch_cf_fn=lambda: ([], "unavailable"),
                fetch_cc_fn=lambda q: ([], "unavailable"),
            )
            res = service.find_similar("Coin change budget problem")
            self.assertEqual(res.leetcode, [])
            self.assertIn("unavailable", res.platform_status["leetcode"])

    def test_all_three_platforms_dedup_and_personalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat_path = Path(tmp) / "lc.json"
            src = Path(tmp) / "src.json"
            src.write_text(
                '['
                '{"task_id": "coin-change", "difficulty": "Medium", "tags": ["dp", "math"], "problem_description": "Fewest coins to reach budget"},'
                '{"task_id": "climbing-stairs", "difficulty": "Easy", "tags": ["dp"], "problem_description": "Ways to climb stairs"}'
                ']',
                encoding="utf-8",
            )
            import_leetcode_json(src, cat_path)

            cf_pool = [
                {"contestId": 189, "index": "A", "name": "Cut Ribbon Budget", "rating": 1300, "tags": ["dp", "math"]},
                {"contestId": 189, "index": "A", "name": "Cut Ribbon Budget", "rating": 1300, "tags": ["dp", "math"]},
            ]
            cc_items = [
                {"code": "CHCOINS", "name": "Chef and Coin Budget", "difficulty_rating": "1400"},
                {"code": "CHCOINS", "name": "Chef and Coin Budget", "difficulty_rating": "1400"},
            ]

            service = SimilarProblemsService(
                llm_service=self.llm,
                embedding_service=self.disabled_emb,
                leetcode_catalog_path=cat_path,
                fetch_cf_fn=lambda: (cf_pool, "live"),
                fetch_cc_fn=lambda q: (cc_items, "live"),
            )

            res = service.find_similar(
                "Maximize items within budget using dp",
                solved_urls=["https://leetcode.com/problems/climbing-stairs/"],
                exclude_solved=True,
            )

            self.assertIn("imported dataset", res.platform_status["leetcode"])
            self.assertEqual(len(res.leetcode), 1)
            self.assertEqual(res.leetcode[0].url, "https://leetcode.com/problems/coin-change/")
            self.assertIn("Progressive difficulty", res.leetcode[0].reason)

            self.assertEqual(res.platform_status["codeforces"], "live")
            self.assertEqual(len(res.codeforces), 1)
            self.assertEqual(res.codeforces[0].url, "https://codeforces.com/problemset/problem/189/A")

            self.assertEqual(res.platform_status["codechef"], "live")
            self.assertEqual(len(res.codechef), 1)
            self.assertEqual(res.codechef[0].url, "https://www.codechef.com/problems/CHCOINS")

    def test_rate_limit_and_api_failure_handled_gracefully(self):
        service = SimilarProblemsService(
            llm_service=self.llm,
            embedding_service=self.disabled_emb,
            leetcode_catalog_path=Path("nonexistent_catalog_12345.json"),
            fetch_cf_fn=lambda: ([], "rate_limited (HTTP 429)"),
            fetch_cc_fn=lambda q: ([], "unavailable (timeout)"),
        )
        res = service.find_similar("Find two sum in array")
        self.assertEqual(res.codeforces, [])
        self.assertEqual(res.codechef, [])
        self.assertEqual(res.platform_status["codeforces"], "rate_limited (HTTP 429)")
        self.assertEqual(res.platform_status["codechef"], "unavailable (timeout)")

    def test_result_caching_avoids_duplicate_fetches(self):
        cf_calls = 0

        def fetch_cf():
            nonlocal cf_calls
            cf_calls += 1
            return ([{"contestId": 1, "index": "A", "name": "Budget DP", "rating": 1200, "tags": ["dp"]}], "live")

        service = SimilarProblemsService(
            llm_service=self.llm,
            embedding_service=self.disabled_emb,
            leetcode_catalog_path=Path("nonexistent_catalog_12345.json"),
            fetch_cf_fn=fetch_cf,
            fetch_cc_fn=lambda q: ([], "live"),
        )
        service.find_similar("Budget DP problem")
        service.find_similar("Budget DP problem")
        self.assertEqual(cf_calls, 1)

        service.find_similar("Budget DP problem", refresh=True)
        self.assertEqual(cf_calls, 2)

    def test_similarity_score_combines_semantic_topic_and_algorithm(self):
        high = compute_similarity_score(
            problem_text="Find maximum coin count within budget",
            extracted_tags=["dp", "math"],
            extracted_algorithms=["knapsack"],
            candidate_title="Budget Coin Knapsack",
            candidate_tags=["dp", "math"],
            semantic_sim=0.85,
        )
        low = compute_similarity_score(
            problem_text="Find maximum coin count within budget",
            extracted_tags=["dp", "math"],
            extracted_algorithms=["knapsack"],
            candidate_title="Shortest Path Tree",
            candidate_tags=["graphs", "trees"],
            semantic_sim=0.10,
        )
        self.assertGreater(high, low)
        self.assertTrue(0 <= low <= 100)
        self.assertTrue(0 <= high <= 100)


if __name__ == "__main__":
    unittest.main()
