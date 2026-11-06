import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def parse_suggestion_json(content: str) -> dict:
    """
    Safely parses JSON feedback from LLM output, extracting JSON
    content even if wrapped in markdown code blocks.
    """
    if not content or not isinstance(content, str):
        return {
            "mistake_type": "unknown",
            "issue": "Empty feedback from AI",
            "hint": "Check your code for syntax and logic errors."
        }

    cleaned = content.strip()
    # Strip markdown code blocks
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

    return {
        "mistake_type": "unknown",
        "issue": content,
        "hint": "Check your code for errors."
    }


def generate_suggestion(
    client: Groq,
    problem: str,
    usercode: str,
    result: dict,
    model: str = None
):
    """
    Analyzes user code failures and generates targeted, constructive hints
    using Groq LLM without giving away the full code.
    """
    if not model:
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if not client:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "mistake_type": "unknown",
                "issue": "GROQ_API_KEY not configured",
                "hint": "Configure your API key to get AI suggestions."
            }
        client = Groq(api_key=api_key)

    prompt = f"""
You are an expert competitive programming mentor.

Analyze the user's code and identify the issue.

========================
INPUT
========================
Problem:
{problem}

User Code:
{usercode}

Result:
{result}

========================
OUTPUT (STRICT JSON ONLY)
========================
{{
  "mistake_type": "...",
  "issue": "...clear explanation...",
  "hint": "...specific fix guidance..."
}}

========================
RULES
========================
- Return ONLY valid JSON
- No extra text
- No explanation outside JSON
- Do NOT give full code
- Be precise and beginner-friendly
"""

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
            max_tokens=500
        )
        content = response.choices[0].message.content
        return parse_suggestion_json(content)

    except Exception as e:
        return {
            "mistake_type": "api_error",
            "issue": f"Failed to generate suggestion: {str(e)}",
            "hint": "Check your code logic manually or retry later."
        }


if __name__ == "__main__":
    sample_prob = "sum of 2 numbers"
    sample_code = "def sum(a,b):\n    return a-b"
    sample_result = {
        "summary": {"verdict": "Wrong Answer", "passed": 0, "total": 1},
        "results": [{"input": {"a": 1, "b": 2}, "expected": 3, "actual": -1}]
    }
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if GROQ_API_KEY:
        cli = Groq(api_key=GROQ_API_KEY)
        res = generate_suggestion(client=cli, problem=sample_prob, usercode=sample_code, result=sample_result, model=GROQ_MODEL)
        print("Suggestion:", res)
    else:
        print("Set GROQ_API_KEY to test directly.")
