import unittest
from unittest.mock import MagicMock
from app.schemas.testcase import TestCase
from app.services.validation_service import ValidationService


class TestValidationService(unittest.TestCase):
    def setUp(self):
        self.mock_judge = MagicMock()
        self.mock_harness = MagicMock()
        self.service = ValidationService(
            judge_service=self.mock_judge,
            harness_service=self.mock_harness,
        )

    def test_validate_reference_solutions_all_valid(self):
        self.mock_harness.detect_function_name.side_effect = ["bruteforce_solve", "optimal_solve"]
        self.mock_harness.build_harness.return_value = "wrapped_code"
        self.mock_judge.submit_raw.return_value = {
            "status": {"description": "Accepted"},
            "stdout": "[0, 1]\n",
        }

        testcases = [TestCase(input={"nums": [2, 7], "target": 9}, expected_output=[0, 1])]
        res = self.service.validate_reference_solutions(
            brute_code="def bruteforce_solve(): pass",
            optimal_code="def optimal_solve(): pass",
            testcases=testcases,
        )

        self.assertEqual(res.valid_count, 1)
        self.assertEqual(res.failed_count, 0)
        self.assertTrue(res.all_valid)
        self.assertEqual(len(res.valid_testcases), 1)

    def test_validate_reference_solutions_mismatch(self):
        self.mock_harness.detect_function_name.side_effect = ["bruteforce_solve", "optimal_solve"]
        self.mock_harness.build_harness.return_value = "wrapped_code"
        # Brute returns [0, 1], optimal returns [0, 0]
        self.mock_judge.submit_raw.side_effect = [
            {"status": {"description": "Accepted"}, "stdout": "[0, 1]\n"},
            {"status": {"description": "Accepted"}, "stdout": "[0, 0]\n"},
        ]

        testcases = [TestCase(input={"nums": [2, 7], "target": 9}, expected_output=[0, 1])]
        res = self.service.validate_reference_solutions(
            brute_code="def bruteforce_solve(): pass",
            optimal_code="def optimal_solve(): pass",
            testcases=testcases,
        )

        self.assertEqual(res.valid_count, 0)
        self.assertEqual(res.failed_count, 1)
        self.assertFalse(res.all_valid)


if __name__ == "__main__":
    unittest.main()
