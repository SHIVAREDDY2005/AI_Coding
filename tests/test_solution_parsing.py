import unittest
from funtions.extract_codes import extract_codes


class TestSolutionParsing(unittest.TestCase):
    def test_extract_codes_standard(self):
        llm_output = """
# BRUTE FORCE SOLUTION
def bruteforce_solve(n):
    return n * 2

# OPTIMAL SOLUTION
def optimal_solve(n):
    return n << 1
"""
        brute, optimal = extract_codes(llm_output)
        self.assertIsNotNone(brute)
        self.assertIsNotNone(optimal)
        self.assertIn("def bruteforce_solve", brute)
        self.assertIn("def optimal_solve", optimal)

    def test_extract_codes_with_markdown_fences(self):
        llm_output = """```python
# BRUTE FORCE SOLUTION
def bruteforce_solve(n):
    return sum(range(n))

# OPTIMAL SOLUTION
def optimal_solve(n):
    return n * (n - 1) // 2
```"""
        brute, optimal = extract_codes(llm_output)
        self.assertIsNotNone(brute)
        self.assertIsNotNone(optimal)
        self.assertFalse(brute.startswith("```"))
        self.assertFalse(optimal.endswith("```"))
        self.assertIn("def bruteforce_solve", brute)
        self.assertIn("def optimal_solve", optimal)

    def test_extract_codes_missing_marker(self):
        llm_output = "def solve(): return 42"
        brute, optimal = extract_codes(llm_output)
        self.assertIsNone(brute)
        self.assertIsNone(optimal)

    def test_extract_codes_empty(self):
        brute, optimal = extract_codes("")
        self.assertIsNone(brute)
        self.assertIsNone(optimal)

        brute, optimal = extract_codes(None)
        self.assertIsNone(brute)
        self.assertIsNone(optimal)


if __name__ == "__main__":
    unittest.main()
