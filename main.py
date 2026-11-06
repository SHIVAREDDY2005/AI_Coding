import os
import sys
from dotenv import load_dotenv

from app.core.config import get_settings
from app.services.harness_service import HarnessService
from app.services.judge_service import JudgeService
from app.services.llm_service import LLMService, LLMServiceError
from app.services.validation_service import ValidationService

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()


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
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY is not configured in .env or environment.")
        sys.exit(1)

    # Initialize reusable services directly (CLI layer)
    harness_service = HarnessService()
    judge_service = JudgeService(settings=settings, harness_service=harness_service)
    llm_service = LLMService(settings=settings)
    validation_service = ValidationService(judge_service=judge_service, harness_service=harness_service)

    # 1. Problem Statement
    print("=" * 60)
    print(f"🎯 {settings.PROJECT_NAME} - Interactive CLI Pipeline")
    print("=" * 60)

    problem = get_multiline_input("\n📝 Step 1: Enter the problem statement:")
    if not problem:
        print("[ERROR] Problem statement cannot be empty.")
        sys.exit(1)

    # 2. Reference Solution Generation
    print(f"\n🧠 Step 2: Generating reference solutions via LLM ({settings.GROQ_MODEL})...")
    try:
        solutions = llm_service.generate_reference_solutions(problem)
    except LLMServiceError as e:
        print(f"[ERROR] Failed to generate reference solutions: {e}")
        sys.exit(1)

    print("\n--- [Brute Force Solution] ---")
    print(solutions.brute_code)
    print("\n--- [Optimal Solution] ---")
    print(solutions.optimal_code)

    # 3. Test Case Generation
    print("\n🧪 Step 3: Generating test cases with AI...")
    try:
        raw_testcases = llm_service.generate_testcases(problem)
    except LLMServiceError as e:
        print(f"[ERROR] Failed to generate test cases: {e}")
        sys.exit(1)

    print(f"[OK] Generated {len(raw_testcases)} test cases.")

    # 4. Reference Solution Validation via Judge0
    print("\n⚖️ Step 4: Validating test cases against reference solutions via Judge0 sandbox...")
    try:
        val_result = validation_service.validate_reference_solutions(
            brute_code=solutions.brute_code,
            optimal_code=solutions.optimal_code,
            testcases=raw_testcases,
        )
    except Exception as e:
        print(f"[ERROR] Validation service error: {e}")
        sys.exit(1)

    if not val_result.valid_testcases:
        print("[ERROR] None of the generated test cases passed reference validation. Aborting.")
        sys.exit(1)

    print(f"[OK] {val_result.valid_count} test cases successfully verified in sandbox.")
    for i, c in enumerate(val_result.valid_testcases, 1):
        print(f"  Test {i}: Input = {c.input} | Expected = {c.expected_output}")

    # 5. User Code Submission
    print("\n" + "=" * 60)
    user_code = get_multiline_input("💻 Step 5: Enter your solution code:")
    if not user_code:
        print("[ERROR] User code cannot be empty.")
        sys.exit(1)

    language = input("Enter programming language (e.g., 'Python 3', 'cpp', 'javascript'):\n").strip()
    if not language:
        language = "Python 3"

    # 6. Judge0 Execution & Test Case Comparison
    print(f"\n⚡ Step 6: Executing user code against {len(val_result.valid_testcases)} verified test cases on Judge0...")
    try:
        eval_result = judge_service.evaluate_code(
            code=user_code,
            language=language,
            testcases=val_result.valid_testcases,
        )
    except Exception as e:
        print(f"[ERROR] Evaluation error: {e}")
        sys.exit(1)

    print("\n📊 Evaluation Summary:")
    print(f"  Verdict: {eval_result.summary.verdict}")
    print(f"  Passed:  {eval_result.summary.passed} / {eval_result.summary.total}")
    print(f"  Function detected: {eval_result.detected_function}")

    # 7. AI Feedback & Suggestions
    if eval_result.summary.verdict == "All Passed":
        print("\n🎉 Congratulations! All test cases passed successfully.")
    else:
        print("\n💡 Step 7: Generating personalized AI suggestion and mistake analysis...")
        try:
            suggestion_res = llm_service.generate_suggestion(
                problem=problem,
                user_code=user_code,
                eval_result=eval_result.model_dump(),
            )
            print("\n" + "-" * 50)
            print("🤖 AI Feedback & Guidance:")
            print(f"  Mistake Type: {suggestion_res.mistake_type}")
            print(f"  Issue:        {suggestion_res.issue}")
            print(f"  Hint:         {suggestion_res.hint}")
            print("-" * 50)
        except Exception as e:
            print(f"[WARN] Could not retrieve AI suggestions: {e}")


if __name__ == "__main__":
    run_cli_pipeline()
