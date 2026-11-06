"""
Backwards-compatibility adapter for code generation.
Delegates to app.services.llm_service.
"""
from groq import Groq
from app.services.llm_service import LLMService, LLMServiceError


def write_code(client: Groq = None, problem_text: str = "", model: str = None):
    service = LLMService(client=client)
    try:
        solutions = service.generate_reference_solutions(problem=problem_text, model=model)
        # Re-assemble formatted raw string for legacy callers
        return f"# BRUTE FORCE SOLUTION\n\n{solutions.brute_code}\n\n# OPTIMAL SOLUTION\n\n{solutions.optimal_code}"
    except LLMServiceError:
        return None
    except Exception:
        return None
