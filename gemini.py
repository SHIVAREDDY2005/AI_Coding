# from google import genai
# from dotenv import load_dotenv
# import os

# # Load variables from .env
# load_dotenv()

# # Get API key
# api_key = os.getenv("GEMINI_API_KEY_1")

# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env file")

# # Create Gemini client
# client = genai.Client(api_key=api_key)

# # List accessible models
# for model in client.models.list():
#     print(model.name)

# response = client.models.generate_content(
#     model="gemini-3.8-flash",
#     contents="Explain binary search in simple terms."
# )

# print(response.text)


import json
import os
import re
import  sys
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
models = client.models.list()

for model in models.data:
    print(model.id)