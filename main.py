import os
import sys
from groq import Groq
from flask.cli import load_dotenv

from funtions.complete_test_cases import generate_testcases, write_code
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from funtions import usercode_evaluation, extract_codes,validate_testcases,suggestion
if __name__ == "__main__":
    client = Groq(api_key=GROQ_API_KEY)
    problem = sys.stdin.read()
    result = write_code.write_code(client, problem)
    code=False
    test=False
    if result:
        brute_code, optimal_code = extract_codes.extract_codes(result)
        print("BRUTE:\n", brute_code)
        print("\nOPTIMAL:\n", optimal_code)
        code=True
    else:
        print("⚠️ Failed to generate solutions")
    testcases = generate_testcases.generate_testcases(client, problem)
    if testcases:
        print("✅ Generated Test Cases:\n")
        for t in testcases:
            print(t)
        test=True
    else:
        print("⚠️ No testcases generated")
    
    if code and test:
        print("\n✅ Code and Test Cases generated successfully!")
        final_testcases=validate_testcases.validate_testcases(brute_code, optimal_code, testcases)
        for case in final_testcases:
            print("\n✅ Validated Test Case:\n", case)

    user_code=input("\nEnter your code:\n")
    language=input("Enter the language (e.g., 'Python 3'):\n")
    result_of_user_code=usercode_evaluation.usercode_evaluation(user_code, final_testcases, language)  # 71 for Python 3
    suggestion_result=suggestion.generate_suggestion(client, problem, user_code, result_of_user_code)