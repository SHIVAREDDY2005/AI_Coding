# Google Gemini & Groq exploratory testing module
#
# from google import genai
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY_1")
# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env file")
# client = genai.Client(api_key=api_key)
# for model in client.models.list():
#     print(model.name)
# response = client.models.generate_content(
#     model="gemini-3.8-flash",
#     contents="Explain binary search in simple terms."
# )
# print(response.text)

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def list_groq_models():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY is not set.")
        return []
    client = Groq(api_key=api_key)
    models = client.models.list()
    return [m.id for m in models.data]


if __name__ == "__main__":
    available = list_groq_models()
    print("Available Groq Models:")
    for model_id in available:
        print(f" - {model_id}")
