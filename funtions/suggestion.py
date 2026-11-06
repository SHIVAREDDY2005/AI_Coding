"""
Backwards-compatibility adapter for suggestion generation.
Delegates to app.services.llm_service.
"""
from groq import Groq
from app.services.llm_service import LLMService, safe_json_parse


def parse_suggestion_json(content: str) -> dict:
    parsed = safe_json_parse(content)
    if isinstance(parsed, dict) and "mistake_type" in parsed:
        return parsed
    return {
        "mistake_type": "unknown",
        "issue": content if content else "Empty feedback from AI",
        "hint": "Check your code for errors."
    }


def generate_suggestion(client: Groq, problem: str, usercode: str, result: dict, model: str = None):
    service = LLMService(client=client)
    res = service.generate_suggestion(problem=problem, user_code=usercode, eval_result=result, model=model)
    return res.model_dump()
