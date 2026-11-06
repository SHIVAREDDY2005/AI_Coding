"""
Backwards-compatibility adapter for testcase generation.
Delegates to app.services.llm_service.
"""
from groq import Groq
from app.services.llm_service import LLMService, LLMServiceError, safe_json_parse


def generate_testcases(client: Groq, problem_text: str, model: str = None):
    service = LLMService(client=client)
    try:
        tcs = service.generate_testcases(problem=problem_text, model=model)
        return [tc.model_dump() for tc in tcs]
    except LLMServiceError:
        return None
    except Exception:
        return None
