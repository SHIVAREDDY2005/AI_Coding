import unittest
from unittest.mock import patch
from funtions.validate_testcases import parse_testcases, validate_testcases


class TestTestCaseValidation(unittest.TestCase):
    def test_parse_testcases_list(self):
        cases = [{"input": 1, "expected_output": 2}]
        self.assertEqual(parse_testcases(cases), cases)

    def test_parse_testcases_json_string(self):
        raw = '[{"input": 1, "expected_output": 2}]'
        cases = parse_testcases(raw)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["expected_output"], 2)

    def test_parse_testcases_dict_with_testcases_key(self):
        raw = '{"testcases": [{"input": 1, "expected_output": 2}]}'
        cases = parse_testcases(raw)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["input"], 1)

    def test_parse_testcases_newline_separated(self):
        raw = """
        {"input": 1, "expected_output": 1}
        {"input": 2, "expected_output": 4}
        """
        cases = parse_testcases(raw)
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[1]["expected_output"], 4)

    @patch("funtions.validate_testcases.submit_to_judge0")
    def test_validate_testcases_mocked_success(self, mock_submit):
        # Brute and optimal both return expected output [0, 1]
        mock_submit.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "[0, 1]\n",
            "stderr": None,
            "compile_output": None
        }

        brute = "def bruteforce_solve(nums, target): return [0, 1]"
        optimal = "def optimal_solve(nums, target): return [0, 1]"
        testcases = [{"input": {"nums": [2, 7], "target": 9}, "expected_output": [0, 1]}]

        valid = validate_testcases(brute, optimal, testcases)
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["input"]["target"], 9)

    @patch("funtions.validate_testcases.submit_to_judge0")
    def test_validate_testcases_mocked_mismatch(self, mock_submit):
        # Optimal returns wrong answer [0, 0]
        mock_submit.side_effect = [
            {"status": {"description": "Accepted"}, "stdout": "[0, 1]\n"},  # Brute
            {"status": {"description": "Accepted"}, "stdout": "[0, 0]\n"},  # Optimal
        ]

        brute = "def bruteforce_solve(nums, target): return [0, 1]"
        optimal = "def optimal_solve(nums, target): return [0, 0]"
        testcases = [{"input": {"nums": [2, 7], "target": 9}, "expected_output": [0, 1]}]

        valid = validate_testcases(brute, optimal, testcases)
        self.assertEqual(len(valid), 0)


if __name__ == "__main__":
    unittest.main()
