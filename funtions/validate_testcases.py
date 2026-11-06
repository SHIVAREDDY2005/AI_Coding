import ast
import json
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from funtions.usercode_evaluation import (
    JUDGE0_HEADERS,
    JUDGE0_URL,
    PythonHarness,
    detect_func_name,
    submit_to_judge0,
)

load_dotenv()


def parse_testcases(raw_text):
    """
    Parses test cases from a Python list, JSON string, or newline-delimited string.
    """
    if isinstance(raw_text, list):
        return raw_text

    if not isinstance(raw_text, str):
        return []

    cleaned = raw_text.strip()
    # Try parsing as JSON first
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "testcases" in data:
            return data["testcases"]
    except Exception:
        pass

    # Try parsing line-by-line (json or literal python dicts)
    cases = []
    for line in cleaned.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except Exception:
            try:
                cases.append(ast.literal_eval(line))
            except Exception as e:
                print("[ERROR] Parse error on testcase line:", line, e)

    return cases


def validate_testcases(
    brute_code: str,
    optimal_code: str,
    testcases,
    judge0_url: str = JUDGE0_URL,
    judge0_headers: dict = None
):
    """
    Validates test cases by running the brute force and optimal solutions
    through Judge0 in a sandboxed environment.

    NO code is executed locally on the host machine.
    """
    if judge0_headers is None:
        judge0_headers = JUDGE0_HEADERS

    parse_cases = parse_testcases(testcases)
    if not parse_cases:
        print("[ERROR] No test cases to validate")
        return []

    if not brute_code or not optimal_code:
        print("[ERROR] Both brute force and optimal code are required for validation")
        return []

    harness = PythonHarness()
    brute_fn = detect_func_name(brute_code, 71) or "bruteforce_solve"
    opt_fn = detect_func_name(optimal_code, 71) or "optimal_solve"

    valid_cases = []
    failed_cases = []

    for case in parse_cases:
        try:
            inp = case.get("input")
            expected = case.get("expected_output", case.get("expected"))

            keys = list(inp.keys()) if isinstance(inp, dict) else []
            stdin_payload = json.dumps(inp)

            # Build harnesses for both solutions
            brute_wrapped = harness.build(brute_code, keys, inp, brute_fn)
            opt_wrapped = harness.build(optimal_code, keys, inp, opt_fn)

            # Submit brute solution to Judge0
            brute_res = submit_to_judge0(brute_wrapped, 71, stdin_payload, url=judge0_url, headers=judge0_headers)
            brute_status = brute_res.get("status", {}).get("description")

            if brute_status != "Accepted":
                failed_cases.append({
                    "case": case,
                    "reason": f"Brute solution failed with {brute_status}",
                    "error": brute_res.get("stderr") or brute_res.get("compile_output")
                })
                continue

            # Submit optimal solution to Judge0
            opt_res = submit_to_judge0(opt_wrapped, 71, stdin_payload, url=judge0_url, headers=judge0_headers)
            opt_status = opt_res.get("status", {}).get("description")

            if opt_status != "Accepted":
                failed_cases.append({
                    "case": case,
                    "reason": f"Optimal solution failed with {opt_status}",
                    "error": opt_res.get("stderr") or opt_res.get("compile_output")
                })
                continue

            # Parse outputs
            brute_out = json.loads(brute_res.get("stdout", "").strip())
            opt_out = json.loads(opt_res.get("stdout", "").strip())

            # Verify against expected
            if brute_out == expected and opt_out == expected:
                valid_cases.append(case)
            else:
                failed_cases.append({
                    "case": case,
                    "expected": expected,
                    "brute_output": brute_out,
                    "optimal_output": opt_out
                })

        except Exception as e:
            failed_cases.append({
                "case": case,
                "error": str(e)
            })

    print(f"[OK] Valid testcases: {len(valid_cases)} | [FAIL] Failed testcases: {len(failed_cases)}")
    return valid_cases


if __name__ == "__main__":
    sample_brute = """def bruteforce_solve(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]"""

    sample_optimal = """def optimal_solve(nums, target):
    num_dict = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_dict:
            return [num_dict[complement], i]
        num_dict[num] = i"""

    sample_tests = [
        {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": [0, 1]},
        {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": [1, 2]}
    ]

    print("Direct test validation:", validate_testcases(sample_brute, sample_optimal, sample_tests))
