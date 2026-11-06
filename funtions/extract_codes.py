import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def extract_codes(llm_output: str):
    """
    Extracts brute-force and optimal code sections from the LLM output.
    Cleans markdown formatting and code fences if present.
    """
    if not llm_output or not isinstance(llm_output, str):
        print("[ERROR] Failed to extract code: Empty or invalid output")
        return None, None

    try:
        cleaned = llm_output.strip()

        # Remove outer markdown fences if the entire output was enclosed in one
        cleaned = re.sub(r"^```(?:python)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        if "# OPTIMAL SOLUTION" not in cleaned:
            print("[ERROR] Failed to extract code: Missing '# OPTIMAL SOLUTION' marker")
            return None, None

        parts = cleaned.split("# OPTIMAL SOLUTION")

        brute_part = parts[0].replace("# BRUTE FORCE SOLUTION", "").strip()
        optimal_part = parts[1].strip()

        # Clean any inner markdown fences within sections
        brute_part = re.sub(r"^```(?:python)?\s*", "", brute_part)
        brute_part = re.sub(r"\s*```$", "", brute_part).strip()

        optimal_part = re.sub(r"^```(?:python)?\s*", "", optimal_part)
        optimal_part = re.sub(r"\s*```$", "", optimal_part).strip()

        print("[OK] Code extraction successful")
        return brute_part, optimal_part

    except Exception as e:
        print(f"[ERROR] Failed to extract code: {e}")
        return None, None


if __name__ == "__main__":
    sample_output = """
# BRUTE FORCE SOLUTION
def bruteforce_solve(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

# OPTIMAL SOLUTION
def optimal_solve(nums, target):
    num_dict = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_dict:
            return [num_dict[complement], i]
        num_dict[num] = i
"""
    brute, optimal = extract_codes(sample_output)
    print("BRUTE:\n", brute)
    print("-----")
    print("OPTIMAL:\n", optimal)
