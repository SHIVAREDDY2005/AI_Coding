import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Support both direct script execution and package imports
try:
    from funtions.complete_test_cases.write_code import write_code
    from funtions.complete_test_cases.generate_testcases import generate_testcases
    from funtions.complete_test_cases.testcase_validation_Judge0 import run_code
except ImportError:
    from write_code import write_code
    from generate_testcases import generate_testcases
    from testcase_validation_Judge0 import run_code


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def run_pipeline():
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in environment.")
        return

    client = Groq(api_key=GROQ_API_KEY)

    # Problem definition
    problem = """
Given an integer n, find the sum of its digits.

Input:
A single integer n.

Constraints:
1 <= n <= 10^9

Output:
Print the sum of the digits of n.
"""

    # 1. Generate code
    print("\n[1/3] Generating code...")
    code = write_code(client, problem, GROQ_MODEL)
    if not code:
        print("❌ Code generation failed")
        return

    print("\n========== GENERATED CODE ==========\n")
    print(code)

    # 2. Generate test cases
    print("\n[2/3] Generating test cases...")
    testcases = generate_testcases(client, problem, GROQ_MODEL)
    if not testcases:
        print("❌ Test case generation failed")
        return

    print("\n========== GENERATED TEST CASES ==========\n")
    for test in testcases:
        print(test)

    # Extract brute force and optimal
    if "# OPTIMAL SOLUTION" not in code:
        print("❌ Could not split solutions")
        return

    brute_code = code.split("# OPTIMAL SOLUTION")[0].replace("# BRUTE FORCE SOLUTION", "").strip()
    optimal_code = code.split("# OPTIMAL SOLUTION")[1].strip()

    # Convert test cases for Judge0 runner
    tests = []
    for test in testcases:
        tests.append({
            "input": str(test.get("input", "")),
            "expected": str(test.get("expected_output", test.get("expected", "")))
        })

    # 3. Run validation on Judge0
    print("\n[3/3] Running validation via Judge0...")
    brute_result = run_code(71, brute_code, tests)
    optimal_result = run_code(71, optimal_code, tests)

    print("\nBRUTE RESULT:", brute_result.get("passed"), "/", brute_result.get("total"), "passed")
    print("OPTIMAL RESULT:", optimal_result.get("passed"), "/", optimal_result.get("total"), "passed")


if __name__ == "__main__":
    run_pipeline()
