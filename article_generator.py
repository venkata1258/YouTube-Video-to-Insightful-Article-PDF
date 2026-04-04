import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_article(transcript_text: str) -> str:
    try:
        prompt = f"""
        Convert the following YouTube transcript into a well-structured article.

        Requirements:
        - Add proper headings
        - Make it clear and readable
        - Remove repetition
        - Keep it engaging

        Transcript:
        {transcript_text}
        """

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"Error generating article: {str(e)}"