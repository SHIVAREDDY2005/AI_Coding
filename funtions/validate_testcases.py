import ast
import ast

def parse_testcases(raw_text):
    # If already list → return directly
    if isinstance(raw_text, list):
        return raw_text

    # If string → parse it
    cases = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                cases.append(ast.literal_eval(line))
            except Exception as e:
                print("❌ Parse error:", line)
    return cases

def validate_testcases(brute_code, optimal_code, testcases):
    parse_cases = parse_testcases(testcases)
    # -------- Load functions dynamically --------
    def load_function(code_str, func_name):
        local_scope = {}
        try:
            exec(code_str, {}, local_scope)
            return local_scope.get(func_name)
        except Exception as e:
            print(f"❌ Error loading {func_name}: {e}")
            return None

    brute_func = load_function(brute_code, "bruteforce_solve")
    optimal_func = load_function(optimal_code, "optimal_solve")

    if not brute_func or not optimal_func:
        print("❌ Failed to load functions")
        return []

    valid_cases = []
    failed_cases = []

    # -------- Normalize output (order-independent if needed) --------
    def normalize(x):
        if isinstance(x, list):
            return sorted(x)
        return x

    # -------- Execute testcases --------
    for case in parse_cases:
        try:
            inp = case["input"]
            expected = case["expected_output"]

            # 🔥 Support ANY input format
            if isinstance(inp, dict):
                brute_out = brute_func(**inp)
                opt_out = optimal_func(**inp)
            elif isinstance(inp, list):
                brute_out = brute_func(*inp)
                opt_out = optimal_func(*inp)
            else:
                brute_out = brute_func(inp)
                opt_out = optimal_func(inp)

            # normalize outputs
            brute_out_n = normalize(brute_out)
            opt_out_n = normalize(opt_out)
            expected_n = normalize(expected)

            # -------- Validation --------
            if brute_out_n == expected_n and opt_out_n == expected_n:
                valid_cases.append(case)
            else:
                failed_cases.append({
                    "case": case,
                    "brute": brute_out,
                    "optimal": opt_out
                })

        except Exception as e:
            failed_cases.append({
                "case": case,
                "error": str(e)
            })

    print(f"✅ Valid: {len(valid_cases)} | ❌ Failed: {len(failed_cases)}")

    return valid_cases

# brute_code = """def bruteforce_solve(nums, target):
#     for i in range(len(nums)):
#         for j in range(i + 1, len(nums)):
#             if nums[i] + nums[j] == target:
#                 return [i, j]"""
# optimal_code = """def optimal_solve(nums, target):
#     num_dict = {}
#     for i, num in enumerate(nums):
#         complement = target - num
#         if complement in num_dict:
#             return [num_dict[complement], i]
#         num_dict[num] = i"""
# testcases="""
# {'input': {'nums': [2, 7, 11, 15], 'target': 9}, 'expected_output': [0, 1]}
# {'input': {'nums': [3, 2, 4], 'target': 6}, 'expected_output': [1, 2]}
# {'input': {'nums': [3, 3], 'target': 6}, 'expected_output': [0, 1]}
# {'input': {'nums': [-1, 0, 1], 'target': 0}, 'expected_output': [0, 2]}
# {'input': {'nums': [0, 0, 3], 'target': 0}, 'expected_output': [0, 1]}
# {'input': {'nums': [5, 7, 11, 15], 'target': 12}, 'expected_output': [0, 1]}
# {'input': {'nums': [1000000000, 1000000000, 1000000000], 'target': 2000000000}, 'expected_output': [0, 1]}
# {'input': {'nums': [-1000000000, -1000000000, -1000000000], 'target': -2000000000}, 'expected_output': [0, 1]}
# {'input': {'nums': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'target': 11}, 'expected_output': [0, 9]}
# {'input': {'nums': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 'target': 11}, 'expected_output': [0, 9]}
# {'input': {'nums': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 'target': 1100}, 'expected_output': [0, 10]}
# {'input': {'nums': [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100], 'target': 1100}, 'expected_output': [0, 9]}
# {'input': {'nums': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 'target': 2}, 'expected_output': [0, 1]}
# {'input': {'nums': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'target': 10}, 'expected_output': [0, 9]}
# {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 0}, 'expected_output': [0, 1]}
# {'input': {'nums': [1000000000, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 1000000000}, 'expected_output': [0, 1]}
# {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, 0, 1000000000], 'target': 1000000000}, 'expected_output': [0, 9]}
# {'input': {'nums': [1000000000, 1000000000, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 2000000000}, 'expected_output': [0, 1]}
# {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, 1000000000, 1000000000], 'target': 2000000000}, 'expected_output': [8, 9]}
# {'input': {'nums': [-1000000000, 1000000000, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 0}, 'expected_output': [0, 1]}
# {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, -1000000000, 1000000000], 'target': 0}, 'expected_output': [8, 9]}
# {'input': {'nums': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 'target': 100}, 'expected_output': [0, 0]}
# {'input': {'nums': [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100], 'target': 1000}, 'expected_output': [0, 0]}"""
# final=validate_testcases(brute_code, optimal_code,testcases)
# print("Valid Test Cases:")
# print(final)
# for case in final:
#     print(case)