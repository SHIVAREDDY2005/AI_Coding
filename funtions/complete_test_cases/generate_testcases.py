import json
import re
from groq import Groq

def safe_json_parse(raw):
    try:
        return json.loads(raw)
    except:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

# -------- LLM Test Case Generator --------
def generate_testcases(
    client: Groq,
    problem_text: str,
    model: str,
):

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
        print("⚠ API error:", e)
        return None

    data = safe_json_parse(raw)

    if data is None:
        print("❌ JSON parse failed")
        print(raw)
        return None
    print("✅ Test case generation successful")
    return data.get("testcases", [])

# -------- Example Usage --------
# import os
# import  sys
# from dotenv import load_dotenv
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if __name__ == "__main__":
#     client = Groq(api_key=GROQ_API_KEY)
#     GROQ_MODEL = os.getenv("GROQ_MODEL")
#     problem = "Given an integer n, find the sum of its digits.Input:A single integer n.Constraints: 1 <= n <= 10^9 Output:Print the sum of the digits of n."
#     testcases = generate_testcases(client, problem, GROQ_MODEL)
#     if testcases:
#         print("✅ Generated Test Cases:\n")
#         for t in testcases:
#             print(t)
#     else:
#         print("⚠️ No testcases generated")