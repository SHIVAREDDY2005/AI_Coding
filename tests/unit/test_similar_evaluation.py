"""
20-case evaluation suite measuring Precision@5 and Recall@5 for the
SimilarProblemsService ranking engine using all-MiniLM-L6-v2 embeddings
against the verified imported LeetCode catalog.
"""
import unittest
from unittest.mock import MagicMock

from app.services.embedding_service import EmbeddingService
from app.services.leetcode_catalog import DEFAULT_LEETCODE_CATALOG_PATH
from app.services.llm_service import LLMService
from app.services.similar_service import SimilarProblemsService, clear_similar_caches


EVAL_CASES = [
    {
        "query": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "tags": ["array", "hash table"],
        "algos": ["hash map", "two sum"],
        "relevant_slugs": {"two-sum", "two-sum-ii-input-array-is-sorted", "3sum", "4sum"},
        "dissimilar_slugs": {"binary-tree-inorder-traversal", "n-queens"},
    },
    {
        "query": "Find the longest substring without repeating characters using a sliding window.",
        "tags": ["string", "sliding window", "hash table"],
        "algos": ["sliding window"],
        "relevant_slugs": {"longest-substring-without-repeating-characters", "minimum-window-substring", "substring-with-concatenation-of-all-words"},
        "dissimilar_slugs": {"merge-two-sorted-lists", "climbing-stairs"},
    },
    {
        "query": "Given a sorted array of distinct integers and a target value, return the index if found using binary search.",
        "tags": ["array", "binary search"],
        "algos": ["binary search"],
        "relevant_slugs": {"search-insert-position", "binary-search", "search-in-rotated-sorted-array", "find-first-and-last-position-of-element-in-sorted-array"},
        "dissimilar_slugs": {"number-of-islands", "valid-parentheses"},
    },
    {
        "query": "Merge k sorted linked lists and return it as one sorted list.",
        "tags": ["linked list", "divide and conquer", "heap (priority queue)"],
        "algos": ["merge sort", "priority queue"],
        "relevant_slugs": {"merge-k-sorted-lists", "merge-two-sorted-lists", "sort-list"},
        "dissimilar_slugs": {"word-search", "coin-change"},
    },
    {
        "query": "Given a string containing just parentheses '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
        "tags": ["string", "stack"],
        "algos": ["stack"],
        "relevant_slugs": {"valid-parentheses", "longest-valid-parentheses", "generate-parentheses"},
        "dissimilar_slugs": {"maximum-subarray", "course-schedule"},
    },
    {
        "query": "Find the contiguous subarray with the largest sum (Kadane's algorithm).",
        "tags": ["array", "dynamic programming", "divide and conquer"],
        "algos": ["kadane", "dynamic programming"],
        "relevant_slugs": {"maximum-subarray", "maximum-product-subarray", "best-time-to-buy-and-sell-stock"},
        "dissimilar_slugs": {"valid-sudoku", "invert-binary-tree"},
    },
    {
        "query": "You are climbing a staircase. It takes n steps to reach the top. Each time you can climb 1 or 2 steps.",
        "tags": ["dynamic programming", "math", "memoization"],
        "algos": ["fibonacci", "dynamic programming"],
        "relevant_slugs": {"climbing-stairs", "min-cost-climbing-stairs", "house-robber", "fibonacci-number"},
        "dissimilar_slugs": {"lru-cache", "rotate-image"},
    },
    {
        "query": "Given an m x n 2D binary grid representing a map of '1's (land) and '0's (water), return the number of islands.",
        "tags": ["depth-first search", "breadth-first search", "union find", "matrix"],
        "algos": ["dfs", "bfs", "flood fill"],
        "relevant_slugs": {"number-of-islands", "max-area-of-island", "surrounded-regions"},
        "dissimilar_slugs": {"roman-to-integer", "powx-n"},
    },
    {
        "query": "Given an array of intervals where intervals[i] = [start, end], merge all overlapping intervals.",
        "tags": ["array", "sorting"],
        "algos": ["interval merging", "sorting"],
        "relevant_slugs": {"merge-intervals", "insert-interval", "non-overlapping-intervals"},
        "dissimilar_slugs": {"same-tree", "add-two-numbers"},
    },
    {
        "query": "Given a binary tree, return the level order traversal of its nodes' values (BFS).",
        "tags": ["tree", "breadth-first search", "binary tree"],
        "algos": ["bfs", "level order traversal"],
        "relevant_slugs": {"binary-tree-level-order-traversal", "binary-tree-zigzag-level-order-traversal", "binary-tree-right-side-view"},
        "dissimilar_slugs": {"jump-game", "container-with-most-water"},
    },
    {
        "query": "Given two words word1 and word2, return the minimum number of operations required to convert word1 to word2 (Edit Distance).",
        "tags": ["string", "dynamic programming"],
        "algos": ["edit distance", "dp"],
        "relevant_slugs": {"edit-distance", "delete-operation-for-two-strings", "distinct-subsequences"},
        "dissimilar_slugs": {"valid-anagram", "single-number"},
    },
    {
        "query": "Given an integer array coins and an integer amount, return the fewest number of coins needed to make up that amount.",
        "tags": ["array", "dynamic programming", "breadth-first search"],
        "algos": ["unbounded knapsack", "dp"],
        "relevant_slugs": {"coin-change", "coin-change-ii", "perfect-squares"},
        "dissimilar_slugs": {"linked-list-cycle", "symmetric-tree"},
    },
    {
        "query": "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.",
        "tags": ["hash table", "linked list", "design"],
        "algos": ["lru cache", "doubly linked list"],
        "relevant_slugs": {"lru-cache", "lfu-cache", "min-stack"},
        "dissimilar_slugs": {"sqrtx", "plus-one"},
    },
    {
        "query": "Determine if a binary tree is a valid binary search tree (BST).",
        "tags": ["tree", "depth-first search", "binary search tree"],
        "algos": ["inorder traversal", "dfs"],
        "relevant_slugs": {"validate-binary-search-tree", "kth-smallest-element-in-a-bst", "recover-binary-search-tree"},
        "dissimilar_slugs": {"trapping-rain-water", "spiral-matrix"},
    },
    {
        "query": "There are a total of numCourses courses you have to take. Some courses have prerequisites. Return true if you can finish all courses (cycle detection in directed graph).",
        "tags": ["depth-first search", "breadth-first search", "graph", "topological sort"],
        "algos": ["topological sort", "kahn", "cycle detection"],
        "relevant_slugs": {"course-schedule", "course-schedule-ii", "find-eventual-safe-states"},
        "dissimilar_slugs": {"palindrome-number", "reverse-integer"},
    },
    {
        "query": "Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
        "tags": ["array", "two pointers", "stack", "monotonic stack"],
        "algos": ["two pointers", "monotonic stack"],
        "relevant_slugs": {"trapping-rain-water", "container-with-most-water", "largest-rectangle-in-histogram"},
        "dissimilar_slugs": {"invert-binary-tree", "implement-trie-prefix-tree"},
    },
    {
        "query": "Implement a trie (prefix tree) with insert, search, and startsWith methods.",
        "tags": ["hash table", "string", "design", "trie"],
        "algos": ["trie", "prefix tree"],
        "relevant_slugs": {"implement-trie-prefix-tree", "design-add-and-search-words-data-structure", "word-search-ii"},
        "dissimilar_slugs": {"remove-duplicates-from-sorted-array", "pascal-s-triangle"},
    },
    {
        "query": "Given an array of distinct integers candidates and a target integer, return all unique combinations of candidates where the chosen numbers sum to target.",
        "tags": ["array", "backtracking"],
        "algos": ["backtracking", "combination sum"],
        "relevant_slugs": {"combination-sum", "combination-sum-ii", "subsets", "permutations"},
        "dissimilar_slugs": {"rotate-list", "excel-sheet-column-number"},
    },
    {
        "query": "Given an unsorted array of integers nums, return the length of the longest consecutive elements sequence in O(n) time.",
        "tags": ["array", "hash table", "union find"],
        "algos": ["hash set", "union find"],
        "relevant_slugs": {"longest-consecutive-sequence", "longest-increasing-subsequence"},
        "dissimilar_slugs": {"zigzag-conversion", "swap-nodes-in-pairs"},
    },
    {
        "query": "Reverse a singly linked list iteratively or recursively.",
        "tags": ["linked list", "recursion"],
        "algos": ["linked list reversal"],
        "relevant_slugs": {"reverse-linked-list", "reverse-linked-list-ii", "reverse-nodes-in-k-group"},
        "dissimilar_slugs": {"wildcard-matching", "jump-game-ii"},
    },
]


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


class TestSimilarRecommendationEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clear_similar_caches()
        cls.embedding_service = EmbeddingService(enabled=True)

    def test_20_case_precision_and_recall_at_5(self):
        self.assertTrue(
            DEFAULT_LEETCODE_CATALOG_PATH.exists(),
            "data/leetcode_catalog.json must exist for evaluation",
        )
        total_p5 = 0.0
        total_r5 = 0.0
        dissimilar_in_top5 = 0

        for case in EVAL_CASES:
            mock_client = MagicMock()
            resp = MagicMock()
            tags_json = ", ".join(f'"{t}"' for t in case["tags"])
            algos_json = ", ".join(f'"{a}"' for a in case["algos"])
            resp.choices = [
                MagicMock(
                    message=MagicMock(
                        content=f'{{"tags": [{tags_json}], "algorithms": [{algos_json}], "keywords": [{algos_json}]}}'
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = resp

            service = SimilarProblemsService(
                llm_service=LLMService(client=mock_client),
                embedding_service=self.embedding_service,
                leetcode_catalog_path=DEFAULT_LEETCODE_CATALOG_PATH,
                fetch_cf_fn=lambda: ([], "skipped"),
                fetch_cc_fn=lambda q: ([], "skipped"),
            )
            res = service.find_similar(case["query"])
            top5_slugs = [_slug_from_url(item.url) for item in res.leetcode[:5]]

            hits = len(set(top5_slugs) & case["relevant_slugs"])
            total_p5 += hits / 5.0
            total_r5 += hits / len(case["relevant_slugs"])
            dissimilar_in_top5 += len(set(top5_slugs) & case["dissimilar_slugs"])

        mean_p5 = total_p5 / len(EVAL_CASES)
        mean_r5 = total_r5 / len(EVAL_CASES)
        print(
            f"\n[EVALUATION 20 CASES] Precision@5={mean_p5:.3f}, Recall@5={mean_r5:.3f}, "
            f"DissimilarInTop5={dissimilar_in_top5}"
        )

        self.assertGreaterEqual(mean_p5, 0.30, f"Precision@5 too low: {mean_p5:.3f}")
        self.assertGreaterEqual(mean_r5, 0.50, f"Recall@5 too low: {mean_r5:.3f}")
        self.assertEqual(dissimilar_in_top5, 0, "Dissimilar problems should not appear in top 5")


if __name__ == "__main__":
    unittest.main()
