"""
Backwards-compatibility adapter for validate_testcases.
Delegates to app.services.validation_service while maintaining mock targets.
"""
import ast
import json
from app.core.config import get_settings
from app.services.harness_service import PythonHarness
from funtions.usercode_evaluation import (
    JUDGE0_HEADERS,
    JUDGE0_URL,
    detect_func_name,
    submit_to_judge0,
)

_settings = get_settings()


def parse_testcases(raw_text):
    if isinstance(raw_text, list):
        return raw_text
    if not isinstance(raw_text, str):
        return []

    cleaned = raw_text.strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "testcases" in data:
            return data["testcases"]
    except Exception:
        pass

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
            except Exception:
                pass
    return cases


def validate_testcases(
    brute_code: str,
    optimal_code: str,
    testcases,
    judge0_url: str = JUDGE0_URL,
    judge0_headers: dict = None,
):
    if judge0_headers is None:
        judge0_headers = JUDGE0_HEADERS

    parse_cases = parse_testcases(testcases)
    if not parse_cases:
        return []

    if not brute_code or not optimal_code:
        return []

    harness = PythonHarness()
    brute_fn = detect_func_name(brute_code, 71) or "bruteforce_solve"
    opt_fn = detect_func_name(optimal_code, 71) or "optimal_solve"

    valid_cases = []

    for case in parse_cases:
        try:
            inp = case.get("input")
            expected = case.get("expected_output", case.get("expected"))

            keys = list(inp.keys()) if isinstance(inp, dict) else []
            stdin_payload = json.dumps(inp)

            brute_wrapped = harness.build(brute_code, keys, inp, brute_fn)
            opt_wrapped = harness.build(optimal_code, keys, inp, opt_fn)

            brute_res = submit_to_judge0(brute_wrapped, 71, stdin_payload, url=judge0_url, headers=judge0_headers)
            if brute_res.get("status", {}).get("description") != "Accepted":
                continue

            opt_res = submit_to_judge0(opt_wrapped, 71, stdin_payload, url=judge0_url, headers=judge0_headers)
            if opt_res.get("status", {}).get("description") != "Accepted":
                continue

            brute_out = json.loads(brute_res.get("stdout", "").strip())
            opt_out = json.loads(opt_res.get("stdout", "").strip())

            if brute_out == expected and opt_out == expected:
                valid_cases.append(case)

        except Exception:
            continue

    return valid_cases


__all__ = [
    "parse_testcases",
    "validate_testcases",
    "submit_to_judge0",
]
