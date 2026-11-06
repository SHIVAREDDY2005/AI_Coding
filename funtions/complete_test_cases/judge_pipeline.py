from groq import Groq
from dotenv import load_dotenv
import os

from write_code import write_code
from generate_testcases import generate_testcases
from testcase_validation_Judge0 import run_code


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

client = Groq(api_key=GROQ_API_KEY)


# ----------------------------------------
# Problem
# ----------------------------------------

problem = """
Given an integer n, find the sum of its digits.

Input:
A single integer n.

Constraints:
1 <= n <= 10^9

Output:
Print the sum of the digits of n.
"""


# ----------------------------------------
# 1. Generate code
# ----------------------------------------

code = write_code(
    client,
    problem,
    GROQ_MODEL
)

if not code:
    print("Code generation failed")
    exit()


print("\n========== GENERATED CODE ==========\n")
print(code)


# ----------------------------------------
# 2. Generate test cases
# ----------------------------------------

testcases = generate_testcases(
    client,
    problem,
    GROQ_MODEL
)

if not testcases:
    print("Test case generation failed")
    exit()


print("\n========== GENERATED TEST CASES ==========\n")

for test in testcases:
    print(test)


# Extract brute force
brute_code = code.split("# OPTIMAL SOLUTION")[0]

brute_code = brute_code.replace(
    "# BRUTE FORCE SOLUTION",
    ""
).strip()


# Extract optimal
optimal_code = code.split("# OPTIMAL SOLUTION")[1].strip()


# Convert test cases
tests = []

for test in testcases:
    tests.append({
        "input": str(test["input"]),
        "expected": str(test["expected_output"])
    })


# Run brute force
brute_result = run_code(
    71,
    brute_code,
    tests
)


# Run optimal
optimal_result = run_code(
    71,
    optimal_code,
    tests
)

print("BRUTE:", brute_result)
print("OPTIMAL:", optimal_result)