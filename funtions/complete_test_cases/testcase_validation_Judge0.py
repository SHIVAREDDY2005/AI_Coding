import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

JUDGE0_URL_BASE64 = os.getenv("JUDGE0_URL_BASE64", "https://ce.judge0.com/submissions?wait=true&base64_encoded=true")


def encode(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def decode(value):
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8")
    except Exception:
        return str(value)


def run_code(language_id, code, test_cases, url=JUDGE0_URL_BASE64, headers=None):
    if headers is None:
        headers = {"Content-Type": "application/json"}

    results = []
    passed = 0

    for test in test_cases:
        stdin_val = test.get("input", "")
        expected_val = str(test.get("expected", test.get("expected_output", ""))).strip()

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "language_id": language_id,
                    "source_code": encode(code),
                    "stdin": encode(stdin_val)
                },
                timeout=30
            )
            result = response.json()
        except Exception as e:
            results.append({
                "input": stdin_val,
                "expected": expected_val,
                "output": "",
                "passed": False,
                "status": "Request Error",
                "error": str(e),
                "compile_error": "",
                "time": None,
                "memory": None
            })
            continue

        # Decode Judge0 Base64 fields
        output = decode(result.get("stdout")).strip()
        error = decode(result.get("stderr")).strip()
        compile_error = decode(result.get("compile_output")).strip()
        status = result.get("status", {}).get("description", "Unknown")

        is_passed = (
            status == "Accepted"
            and output == expected_val
        )

        if is_passed:
            passed += 1

        results.append({
            "input": stdin_val,
            "expected": expected_val,
            "output": output,
            "passed": is_passed,
            "status": status,
            "error": error,
            "compile_error": compile_error,
            "time": result.get("time"),
            "memory": result.get("memory")
        })

    return {
        "valid": passed == len(test_cases) if test_cases else False,
        "passed": passed,
        "total": len(test_cases),
        "results": results
    }


if __name__ == "__main__":
    # Example execution: only runs when directly executing this file, NOT on import!
    sample_result = run_code(
        54,
        """
        #include <iostream>
        using namespace std;

        int main() {
            int a, b;
            cin >> a >> b;
            cout << a + b;
            return 0;
        }
        """,
        [
            {"input": "5 7", "expected": "12"},
            {"input": "10 20", "expected": "30"}
        ]
    )
    print("Test run result:", sample_result)
