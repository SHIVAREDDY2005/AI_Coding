import os
import sys
from dotenv import load_dotenv
from groq import Groq

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()


def write_code(
    client: Groq = None,
    problem_text: str = "",
    model: str = None
):
    """
    Generates reference Python solutions (Brute Force and Optimal) using Groq LLM.
    """
    if not model:
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if not client:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[ERROR] GROQ_API_KEY is missing")
            return None
        client = Groq(api_key=api_key)

    prompt = f"""
You are a STRICT competitive programming code generator.

-------------------------------------
VALIDATION RULE:
If the problem is unclear or missing:
- input format
- constraints
- expected output

Then RETURN ONLY:
INVALID_PROBLEM

DO NOT guess anything.
-------------------------------------

TASK:
Generate TWO Python solutions:

1. Brute Force
2. Optimal

-------------------------------------
RULES:
- Only Python code
- No explanation
- No extra text
- No markdown
- No comments except section headers
- Use function-based solutions
- Must handle all constraints
- Must be correct and executable
- USE FUNCTION NAME: bruteforce_solve for brute force
- USE FUNCTION NAME: optimal_solve for optimal solution

-------------------------------------

PROBLEM:
{problem_text}

-------------------------------------

OUTPUT FORMAT (STRICT):

# BRUTE FORCE SOLUTION

def bruteforce_solve(nums, target):
    # solution logic
    ...


# OPTIMAL SOLUTION

def optimal_solve(nums, target):
    # solution logic
    ...

-------------------------------------

FINAL REQUIREMENTS:
- Return ONLY the two Python solutions.
- Do NOT add explanations.
- Do NOT add markdown code fences.
"""

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=model,
            temperature=0.3,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        if "INVALID_PROBLEM" in content.strip():
            print("[WARN] Problem description was rejected as invalid/incomplete")
            return None

        print("[OK] Code generation successful")
        return content

    except Exception as e:
        print("[WARN] API error:", e)
        return None


if __name__ == "__main__":
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if GROQ_API_KEY:
        cli = Groq(api_key=GROQ_API_KEY)
        sample_problem = """
Given an integer n, find the sum of its digits.
Input: A single integer n.
Constraints: 1 <= n <= 10^9
Output: Print the sum of the digits of n.
"""
        res = write_code(cli, sample_problem, GROQ_MODEL)
        print("\n========== GENERATED CODE ==========\n")
        print(res)
    else:
        print("Set GROQ_API_KEY in .env to test directly.")
