import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models for your API key...")
try:
    # Use the client to list models
    for m in client.models.list():
        if "gemma" in m.name.lower():
            print(f"ID: {m.name} | Display Name: {m.display_name}")
except Exception as e:
    print("Error listing models:", e)
