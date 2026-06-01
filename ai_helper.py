import time
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_ai(prompt):
    models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]

    for model_name in models:

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )

            return response.text

        except Exception as e:

            if "503" in str(e):

                time.sleep(5)

                continue

            return f"AI Error: {e}"

    return "Gemini servers are busy. Please try again in a few seconds."
