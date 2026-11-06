import requests
import base64


def encode(value):
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def decode(value):
    if not value:
        return ""

    try:
        return base64.b64decode(value).decode("utf-8")
    except Exception:
        return value


def run_code(language_id, code, test_cases):

    url = "https://ce.judge0.com/submissions?wait=true&base64_encoded=true"

    results = []
    passed = 0

    for test in test_cases:

        response = requests.post(
            url,
            json={
                "language_id": language_id,
                "source_code": encode(code),
                "stdin": encode(test["input"])
            },
            timeout=30
        )

        result = response.json()

        # Decode Judge0 Base64 fields
        output = decode(result.get("stdout")).strip()
        error = decode(result.get("stderr")).strip()
        compile_error = decode(result.get("compile_output")).strip()

        expected = test["expected"].strip()

        status = result.get("status", {}).get("description")

        is_passed = (
            status == "Accepted"
            and output == expected
        )

        if is_passed:
            passed += 1

        results.append({
            "input": test["input"],
            "expected": expected,
            "output": output,
            "passed": is_passed,
            "status": status,
            "error": error,
            "compile_error": compile_error,
            "time": result.get("time"),
            "memory": result.get("memory")
        })

    return {
        "valid": passed == len(test_cases),
        "passed": passed,
        "total": len(test_cases),
        "results": results
    }


#funtion to run C++ code
result = run_code(
    54,
    """
    #include <iostream>
    using namespace std;

    int main() {
        int a, b;
        cin >> a >> b;
        cout << ab + b;
    }
    """,
    [
        {"input": "5 7", "expected": "12"},
        {"input": "10 20", "expected": "30"}
    ]
)

print(result)


# result = run_code(
#     62,
#     """
#     import java.util.Scanner;

#     public class Main {
#         public static void main(String[] args) {
#             Scanner sc = new Scanner(System.in);

#             int a = sc.nextInt();
#             int b = sc.nextInt();

#             System.out.println(a + b);
#         }
#     }
#     """,
#     [
#         {"input": "5 7", "expected": "12"},
#         {"input": "10 20", "expected": "30"}
#     ]
# )

# print(result)



# result = run_code(
#     71,
#     """
# a, b = map(int, input().split())
# print(a + b)
#     """,
#     [
#         {"input": "5 7", "expected": "12"},
#         {"input": "10 20", "expected": "30"}
#     ]
# )

# print(result)