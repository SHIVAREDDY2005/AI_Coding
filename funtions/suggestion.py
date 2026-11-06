
import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq
load_dotenv()

def generate_suggestion(client: Groq, problem: str, usercode: str, result: dict, model: str = "llama-3.3-70b-versatile"):
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

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=500
    )
    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return {
            "mistake_type": "unknown",
            "issue": content,
            "hint": "Check your code for errors."
        }


# -------- Main --------


# if __name__ == "__main__":
#     problem="sum of  2  numbers"
#     usercode="def  sum(a,b):\n    return a-b"
#     result = {
#         "brute": [1, 2],
#         "expected": [3],
#         "actual_output": [-1]
#     }
#     load_dotenv()
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#     client = Groq(api_key=GROQ_API_KEY)
#     res=generate_suggestion(client=Groq(api_key=GROQ_API_KEY), problem=problem, usercode=usercode, result=result)
#     print(res)