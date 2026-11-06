from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


# -------- LLM Code Generator --------
def write_code(
    client: Groq,
    problem_text: str,
    model: str = "openai/gpt-oss-120b"
):

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

IMPORTANT:
Each solution MUST call its function using:

if __name__ == "__main__":
    bruteforce_solve()

for the brute force solution.

And:

if __name__ == "__main__":
    optimal_solve()

for the optimal solution.

The generated code MUST be directly executable when sent to Judge0.

DO NOT only define the functions.
The functions MUST actually be called.

-------------------------------------

PROBLEM:
{problem_text}

-------------------------------------

OUTPUT FORMAT (STRICT):

# BRUTE FORCE SOLUTION

def bruteforce_solve():
    # solution
    ...

if __name__ == "__main__":
    bruteforce_solve()


# OPTIMAL SOLUTION

def optimal_solve():
    # solution
    ...

if __name__ == "__main__":
    optimal_solve()

-------------------------------------

FINAL REQUIREMENTS:
- Return ONLY the two Python solutions.
- Do NOT add explanations.
- Do NOT add markdown code fences.
- Do NOT omit the function calls.
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

        print("✅ Code generation successful")
        return response.choices[0].message.content

    except Exception as e:
        print("⚠ API error:", e)
        return None



# -------- Test This File Directly --------
# if __name__ == "__main__":

#     problem = """
#     Given an integer n, find the sum of its digits.

#     Input:
#     A single integer n.

#     Constraints:
#     1 <= n <= 10^9

#     Output:
#     Print the sum of the digits of n.
#     """

#     result = write_code(client, problem)

#     print("\n========== GENERATED CODE ==========\n")

#     if result:
#         print(result)
#     else:
#         print("⚠️ Failed to generate solutions")