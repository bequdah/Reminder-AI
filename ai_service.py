import os
import json
from google import genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configure the New Gemini/Gemma API Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemma-4-31b-it" 

def parse_task_description(description: str, history: list = None):
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Format history for context
    context = ""
    if history:
        for msg in history:
            role = "User" if msg['type'] == 'user' else "AI"
            context += f"{role}: {msg['text']}\n"

    prompt = f"""
    Today's date is {current_date}.
    You are a friendly, supportive assistant. Speak like a close friend in simple ARABIC.
    
    Conversation History:
    {context}
    
    User's New Input: "{description}"
    
    Instructions:
    1. Keep it extremely SIMPLE. NO technical jargon (No "preprocessing", "stages", "phases").
    2. Act like a friend who is just checking in. Example: "ضللك يومين عالتسليم، شد حيلك!"
    3. Generate 3-5 reminders that sound natural and casual.
    4. Return a JSON object with:
       - "task_name": string
       - "start_date": "YYYY-MM-DD"
       - "end_date": "YYYY-MM-DD"
       - "effort_level": "Low/Medium/High"
       - "brief_summary": "Friendly and very short summary (1 sentence max)"
       - "suggested_reminders": [{{"date": "YYYY-MM-DD", "friendly_message": "Very short friendly message"}}]
    
    Respond ONLY with JSON.
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
            }
        )
        
        if response.text:
            return json.loads(response.text)
        return None
        
    except Exception as e:
        print(f"DEBUG AI ERROR: {e}")
        return None
