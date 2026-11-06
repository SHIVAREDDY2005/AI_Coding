import os
import sys
from dotenv import load_dotenv
from groq import Groq

from funtions import extract_codes, suggestion, usercode_evaluation, validate_testcases
from funtions.complete_test_cases import generate_testcases, write_code

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def get_multiline_input(prompt: str, end_sentinel: str = "END") -> str:
    print(prompt)
    print(f"(Type or paste your text. When finished, enter '{end_sentinel}' on a new line):")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == end_sentinel:
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines).strip()


def run_cli_pipeline():
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY is not configured in .env or environment.")
        sys.exit(1)

    client = Groq(api_key=GROQ_API_KEY)

    # 1. Problem Statement
    print("=" * 60)
    print("🎯 AI Coding Platform - Problem Practice Pipeline")
    print("=" * 60)

    problem = get_multiline_input("\n📝 Step 1: Enter the problem statement:")
    if not problem:
        print("❌ Error: Problem statement cannot be empty.")
        sys.exit(1)

    # 2. Reference Solution Generation
    print("\n🧠 Step 2: Generating reference solutions (Brute Force & Optimal)...")
    code_raw = write_code.write_code(client, problem, GROQ_MODEL)
    if not code_raw:
        print("❌ Failed to generate reference solutions. Aborting.")
        sys.exit(1)

    brute_code, optimal_code = extract_codes.extract_codes(code_raw)
    if not brute_code or not optimal_code:
        print("❌ Failed to extract brute force and optimal solutions. Aborting.")
        sys.exit(1)

    print("\n--- [Brute Force Solution] ---")
    print(brute_code)
    print("\n--- [Optimal Solution] ---")
    print(optimal_code)

    # 3. Test Case Generation
    print("\n🧪 Step 3: Generating test cases with AI...")
    raw_testcases = generate_testcases.generate_testcases(client, problem, GROQ_MODEL)
    if not raw_testcases:
        print("❌ Failed to generate test cases. Aborting.")
        sys.exit(1)

    print(f"✅ Generated {len(raw_testcases)} test cases.")

    # 4. Reference Solution Validation via Judge0
    print("\n⚖️ Step 4: Validating test cases against reference solutions via Judge0...")
    validated_cases = validate_testcases.validate_testcases(brute_code, optimal_code, raw_testcases)
    if not validated_cases:
        print("❌ Error: None of the generated test cases passed reference validation. Aborting.")
        sys.exit(1)

    print(f"✅ {len(validated_cases)} test cases successfully verified with reference solutions.")
    for i, c in enumerate(validated_cases, 1):
        print(f"  Test {i}: Input = {c.get('input')} | Expected = {c.get('expected_output', c.get('expected'))}")

    # 5. User Code Submission
    print("\n" + "=" * 60)
    user_code = get_multiline_input("💻 Step 5: Enter your solution code:")
    if not user_code:
        print("❌ Error: User code cannot be empty.")
        sys.exit(1)

    language = input("Enter programming language (e.g., 'Python 3', 'cpp', 'javascript'):\n").strip()
    if not language:
        language = "Python 3"

    # 6. Judge0 Execution & Test Case Comparison
    print(f"\n⚡ Step 6: Executing user code against {len(validated_cases)} test cases on Judge0...")
    try:
        eval_result = usercode_evaluation.evaluate_user_code(user_code, validated_cases, language)
    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        sys.exit(1)

    summary = eval_result.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", len(validated_cases))
    verdict = summary.get("verdict", "Unknown")

    print("\n📊 Evaluation Summary:")
    print(f"  Verdict: {verdict}")
    print(f"  Passed:  {passed} / {total}")
    print(f"  Function detected: {eval_result.get('detected_function')}")

    # 7. AI Feedback & Suggestions
    if verdict == "All Passed":
        print("\n🎉 Congratulations! All test cases passed successfully.")
    else:
        print("\n💡 Step 7: Generating personalized AI suggestion and mistake analysis...")
        suggestion_res = suggestion.generate_suggestion(client, problem, user_code, eval_result, GROQ_MODEL)
        print("\n" + "-" * 50)
        print("🤖 AI Feedback & Guidance:")
        print(f"  Mistake Type: {suggestion_res.get('mistake_type')}")
        print(f"  Issue:        {suggestion_res.get('issue')}")
        print(f"  Hint:         {suggestion_res.get('hint')}")
        print("-" * 50)


if __name__ == "__main__":
    run_cli_pipeline()
