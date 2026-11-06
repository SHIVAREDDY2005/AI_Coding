import json
import os
import re
import sys
from dotenv import load_dotenv
from groq import Groq

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()


def safe_json_parse(raw: str):
    """
    Safely parses JSON from an LLM response string, stripping
    markdown code fences and extracting JSON blocks if needed.
    """
    if not raw or not isinstance(raw, str):
        return None

    cleaned = raw.strip()

    # Strip outer markdown code blocks ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        # Try finding the first JSON object or array structure
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None


def generate_testcases(
    client: Groq,
    problem_text: str,
    model: str = None,
):
    """
    Generates test cases for a problem statement using Groq LLM.
    Returns a list of testcase dicts: [{'input': ..., 'expected_output': ...}, ...]
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
You are a STRICT competitive programming test case generator.

YOUR JOB:
Generate test cases ONLY if the problem is clearly defined.

-------------------------------------
VALIDATION RULE (VERY IMPORTANT):
If the problem is unclear, incomplete, or missing:
- input definition
- constraints
- expected operation

Then RETURN ONLY:
{{ "error": "Invalid problem description" }}

DO NOT guess the problem.
DO NOT assume anything.
-------------------------------------

PROBLEM:
{problem_text}

-------------------------------------
GENERATION RULES:
- Input MUST follow the problem definition EXACTLY
- If input is defined as a single integer → generate ONLY integers
- DO NOT generate strings, arrays, or random formats unless specified
- Follow constraints strictly
- All numbers must be plain integers
- DO NOT use expressions (like 10**9, 2*10^4)
- Convert everything to actual numeric values
- Include:
  • edge cases
  • boundary values
  • tricky cases
  • random valid cases
-------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "testcases": [
    {{
      "input": 123,
      "expected_output": 321
    }}
  ]
}}

-------------------------------------
STRICT OUTPUT RULES:
- No explanation
- No extra text
- No markdown
- No comments
- Only valid JSON
-------------------------------------

Generate at least 10 testcases.
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.6,
            max_tokens=2000
        )

        raw = response.choices[0].message.content

    except Exception as e:
        print("[WARN] API error:", e)
        return None

    data = safe_json_parse(raw)

    if data is None:
        print("[ERROR] JSON parse failed")
        return None

    if isinstance(data, dict) and "error" in data:
        print(f"[WARN] Validation error from generator: {data['error']}")
        return None

    testcases = data.get("testcases", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    print(f"[OK] Test case generation successful ({len(testcases)} cases)")
    return testcases


if __name__ == "__main__":
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if GROQ_API_KEY:
        cli = Groq(api_key=GROQ_API_KEY)
        sample_problem = "Given an integer n, find the sum of its digits. Input: A single integer n. Constraints: 1 <= n <= 10^9. Output: Print the sum of the digits of n."
        tcs = generate_testcases(cli, sample_problem, GROQ_MODEL)
        print("Generated:", tcs)
    else:
        print("Set GROQ_API_KEY in .env to test directly.")
