"""
Backwards-compatibility adapter for extract_codes.
Delegates to app.services.llm_service.
"""
from app.services.llm_service import LLMService, LLMServiceError

_llm_service = LLMService()


def extract_codes(llm_output: str):
    if not llm_output or not isinstance(llm_output, str):
        return None, None
    try:
        solutions = _llm_service.extract_solutions(llm_output)
        return solutions.brute_code, solutions.optimal_code
    except LLMServiceError:
        return None, None
    except Exception:
        return None, None
