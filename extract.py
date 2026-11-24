import os
import sys 
from pathlib import Path

from google import genai
from google.genai import types

from schema import Extracted

from dotenv import load_dotenv

load_dotenv()

#loading gemini api key from .env
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Gemini api key not found.",file=sys.stderr)
    sys.exit(1)

#loading gemini model from .env
gemini_model = os.getenv("GEMINI_MODEL")
if not gemini_model:
    print("GEMINI_MODEL is missing", file=sys.stderr)
    sys.exit(1)


if len(sys.argv) < 2:
    print("Usage, uv run extract.py \"event listing raw text\"",file=sys.stderr)
    sys.exit(1)


event_text = " ".join(sys.argv[1:]).strip()


prompt_path = Path("prompts/extract.txt")
prompt = prompt_path.read_text(encoding="utf-8")


def ask_gemini(event_text,prompt,api_key,gemini_model):
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=prompt,
        response_mime_type="application/json",
        response_schema=Extracted
    )

    response = client.models.generate_content(
        model=gemini_model,
        contents=event_text,
        config=config,
    )


    return response.text,response.parsed



json_text, extracted_data = ask_gemini(
    event_text,
    prompt,
    gemini_api_key,
    gemini_model,
)

print(json_text)