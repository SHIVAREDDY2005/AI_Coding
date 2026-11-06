def extract_codes(llm_output):
    try:
        parts = llm_output.split("# OPTIMAL SOLUTION")

        brute_part = parts[0].replace("# BRUTE FORCE SOLUTION", "").strip()
        optimal_part = parts[1].strip()
        print("✅ Code extraction successful")
        return brute_part, optimal_part

    except:
        print("❌ Failed to extract code")
        return None, None


llm_output = """
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

# brute_code, optimal_code = extract_codes(llm_output)

# print(brute_code)
# print("-----")
# print(optimal_code)