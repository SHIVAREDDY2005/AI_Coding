import json
import re
from typing import Any, Optional
from groq import Groq

from app.core.config import Settings, get_settings
from app.schemas.solution import ExtractedSolutions
from app.schemas.suggestion import SuggestionResponse
from app.schemas.testcase import TestCase


class LLMServiceError(Exception):
    """Raised when LLM generation fails."""
    pass


def safe_json_parse(raw: str) -> Optional[Any]:
    if not raw or not isinstance(raw, str):
        return None

    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None


def _extract_partial_testcases(raw: str) -> list[dict[str, Any]]:
    """
    Recovers complete testcase objects from a partially truncated JSON response.
    """
    if not raw or not isinstance(raw, str):
        return []
    decoder = json.JSONDecoder()
    recovered: list[dict[str, Any]] = []
    idx = 0
    while idx < len(raw):
        brace = raw.find("{", idx)
        if brace == -1:
            break
        try:
            obj, end_idx = decoder.raw_decode(raw, brace)
            if isinstance(obj, dict) and "input" in obj:
                recovered.append(obj)
                idx = end_idx
                continue
        except Exception:
            pass
        idx = brace + 1
    return recovered


class LLMService:
    """
    Service responsible for all AI model interactions (Groq / Gemini)
    including code generation, test case synthesis, and mentoring hints.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        client: Optional[Groq] = None,
    ):
        self.settings = settings or get_settings()
        self._client = client

    @property
    def client(self) -> Groq:
        if self._client is None:
            if not self.settings.GROQ_API_KEY:
                raise LLMServiceError("GROQ_API_KEY is not configured")
            self._client = Groq(api_key=self.settings.GROQ_API_KEY)
        return self._client

    def extract_solutions(self, llm_output: str) -> ExtractedSolutions:
        """
        Extracts brute-force and optimal code sections from raw LLM output.
        """
        if not llm_output or not isinstance(llm_output, str):
            raise LLMServiceError("Empty or invalid output from code generation model")

        cleaned = llm_output.strip()
        cleaned = re.sub(r"^```(?:python)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        if "# OPTIMAL SOLUTION" not in cleaned:
            raise LLMServiceError("Missing '# OPTIMAL SOLUTION' marker in generated code")

        parts = cleaned.split("# OPTIMAL SOLUTION")
        brute_part = parts[0].replace("# BRUTE FORCE SOLUTION", "").strip()
        optimal_part = parts[1].strip()

        brute_part = re.sub(r"^```(?:python)?\s*", "", brute_part)
        brute_part = re.sub(r"\s*```$", "", brute_part).strip()

        optimal_part = re.sub(r"^```(?:python)?\s*", "", optimal_part)
        optimal_part = re.sub(r"\s*```$", "", optimal_part).strip()

        if not brute_part or not optimal_part:
            raise LLMServiceError("Failed to extract valid code blocks for both solutions")

        return ExtractedSolutions(brute_code=brute_part, optimal_code=optimal_part)

    def generate_reference_solutions(
        self,
        problem: str,
        model: Optional[str] = None,
    ) -> ExtractedSolutions:
        """
        Generates reference Python solutions (Brute Force & Optimal) using Groq LLM.
        """
        target_model = model or self.settings.GROQ_MODEL

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
{problem}

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
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=target_model,
                temperature=0.3,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content
        except Exception as e:
            raise LLMServiceError(f"Groq API error during solution generation: {str(e)}") from e

        if "INVALID_PROBLEM" in raw.strip():
            raise LLMServiceError("Problem description was rejected as invalid or incomplete")

        return self.extract_solutions(raw)

    def generate_testcases(
        self,
        problem: str,
        model: Optional[str] = None,
    ) -> list[TestCase]:
        """
        Generates competitive programming test cases using Groq LLM.
        """
        target_model = model or self.settings.GROQ_MODEL

        prompt = f"""
You are a STRICT competitive programming test case generator.

YOUR JOB:
Generate test cases ONLY if the problem is clearly defined.

-------------------------------------
VALIDATION RULE:
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
{problem}

-------------------------------------
GENERATION RULES:
- Input MUST follow the problem definition EXACTLY
- If the problem has multiple input parameters (e.g. n, arr, target), "input" MUST be a JSON object with those parameter names as keys, e.g. {{"n": 5, "arr": [1, 2, 3, 4, 5], "target": 9}}
- If the problem has a single input parameter (e.g. an integer n or an array nums), use that JSON value directly (e.g. 123 or [1, 2, 3])
- NEVER pack arrays or multiple inputs into a newline-delimited string like "5\n1 2 3"
- Follow constraints strictly
- Keep array/list/string sizes compact (at most 15 elements) so JSON stays valid and concise
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

Generate at least 8 testcases.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=target_model,
                temperature=0.3,
                max_tokens=8000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
        except Exception as e:
            raise LLMServiceError(f"Groq API error during testcase generation: {str(e)}") from e

        data = safe_json_parse(raw)
        if data is None:
            partial = _extract_partial_testcases(raw)
            if partial:
                data = {"testcases": partial}
            else:
                raise LLMServiceError("Failed to parse JSON test cases from model response")

        if isinstance(data, dict) and "error" in data:
            raise LLMServiceError(f"Model rejected problem: {data['error']}")

        raw_cases = (
            data.get("testcases", [])
            if isinstance(data, dict)
            else (data if isinstance(data, list) else [])
        )

        testcases: list[TestCase] = []
        for rc in raw_cases:
            if isinstance(rc, dict) and "input" in rc:
                exp = rc.get("expected_output", rc.get("expected"))
                testcases.append(TestCase(input=rc["input"], expected_output=exp))

        if not testcases:
            raise LLMServiceError("Zero valid test cases generated by model")

        return testcases

    def generate_suggestion(
        self,
        problem: str,
        user_code: str,
        eval_result: dict,
        model: Optional[str] = None,
        language: Optional[str] = None,
        testcases: Optional[list[dict[str, Any]]] = None,
        feedback_focus: Optional[str] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
    ) -> SuggestionResponse:
        """
        Analyzes user code, test cases, and evaluation results to generate
        targeted debugging or optimization feedback according to the user's request.
        """
        target_model = model or self.settings.GROQ_MODEL
        lang_label = language or "Not specified"
        focus_label = (
            feedback_focus.strip()
            if feedback_focus and feedback_focus.strip()
            else "Automatic: diagnose any failing test cases or errors first; if tests pass or have not run yet, review correctness on the test cases and suggest time/space optimizations."
        )
        testcases_block = (
            json.dumps(testcases[:10], indent=2)
            if testcases
            else "No test cases provided."
        )
        history_block = (
            "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in conversation_history[-6:]
            )
            if conversation_history
            else "None (first message in conversation)."
        )

        prompt = f"""
You are an expert competitive programming mentor.

Analyze the user's ACTUAL written code, the problem statement, the workspace test cases, and the latest execution result.
Respond directly to what the user asked for in "User Feedback Request", taking into account the prior conversation if any.

========================
INPUT
========================
Problem:
{problem}

Language: {lang_label}

User Code:
{user_code}

Workspace Test Cases (sample):
{testcases_block}

Latest Execution Result:
{json.dumps(eval_result, default=str)}

Previous Conversation:
{history_block}

User Feedback Request:
{focus_label}

========================
OUTPUT (STRICT JSON ONLY)
========================
{{
  "mistake_type": "short category such as logic_error, syntax_error, runtime_error, edge_case, optimization, or code_review",
  "issue": "clear, accurate assessment referencing the user's actual code and test cases (do NOT invent unrelated bugs if the code is correct)",
  "hint": "specific, actionable guidance answering the user's feedback request without dumping the complete solution code",
  "complexity": "estimated current time and space complexity of the user's code",
  "optimization": "concrete way to optimize time/space complexity or handle edge cases for this specific code and problem"
}}

========================
RULES
========================
- Return ONLY valid JSON
- No extra text or markdown outside JSON
- Ground your response strictly in the User Code and Workspace Test Cases above
- If all tests passed or the user asks for optimization, focus on complexity and optimization instead of inventing bugs
- Do NOT give full copy-paste solution code
- Be precise, practical, and tailored to the user's request
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=target_model,
                temperature=0.3,
                max_tokens=900,
            )
            content = response.choices[0].message.content
        except Exception as e:
            raise LLMServiceError(f"Groq API error during suggestion generation: {str(e)}") from e

        parsed = safe_json_parse(content)
        if isinstance(parsed, dict) and ("mistake_type" in parsed or "issue" in parsed or "hint" in parsed):
            return SuggestionResponse(
                mistake_type=str(parsed.get("mistake_type") or "code_review"),
                issue=str(parsed.get("issue") or "Reviewed your code against the problem and test cases."),
                hint=str(parsed.get("hint") or "Check edge cases and complexity."),
                complexity=str(parsed["complexity"]) if parsed.get("complexity") else None,
                optimization=str(parsed["optimization"]) if parsed.get("optimization") else None,
                model_used=target_model,
            )

        return SuggestionResponse(
            mistake_type="logic_error",
            issue=content if content else "Failed test cases detected.",
            hint="Check variable types, loop bounds, and corner cases.",
            model_used=target_model,
        )
