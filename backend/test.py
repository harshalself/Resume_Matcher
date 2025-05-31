import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY is missing")

genai.configure(api_key=api_key)

try:
    # Swap to flash model to reduce load
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
  # or any other available model

    response = model.generate_content("Say hello like a pirate!")
    print("[SUCCESS] Response:\n")
    print(response.text)

except Exception as e:
    print("[ERROR] An error occurred:")
    print(e)
