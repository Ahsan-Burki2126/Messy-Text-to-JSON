import os
import sys 
from pathlib import Path

from google import genai
from google.genai import types
from google.genai import errors
from schema import Extracted
from pydantic import ValidationError
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
if not event_text:
    print("Event listing cannot be empty.", file=sys.stderr)
    sys.exit(1)

prompt_path = Path("prompts/extract.txt")
prompt = prompt_path.read_text(encoding="utf-8")


def ask_gemini(
    event_text,
    prompt,
    api_key,
    gemini_model,
    validation_error=None,
):
    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=prompt,
        response_mime_type="application/json",
        response_schema=Extracted,
    )

    contents = event_text

    if validation_error:
        contents = (
            f"{event_text}\n\n"
            f"The previous response failed validation.\n"
            f"Validation error:\n{validation_error}\n"
            f"Correct the response and return only valid structured data."
        )

    response = client.models.generate_content(
        model=gemini_model,
        contents=contents,
        config=config,
    )

    return response.text, response.parsed


def validate_extraction(json_text):
    try:
        extracted = Extracted.model_validate_json(json_text)
        return extracted, None
    except ValidationError as error:
        return None, str(error)


MAX_ATTEMPTS = 3

validation_error = None

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        json_text, _ = ask_gemini(
            event_text,
            prompt,
            gemini_api_key,
            gemini_model,
            validation_error=validation_error,
        )
    except errors.ServerError:
            print(
        "Gemini server is temporarily unavailable. Please try again later.",
        file=sys.stderr,
    )
            sys.exit(1)
    except errors.ClientError as error:
        print(
            f"Gemini rejected the request. Check the model name and API key.\n{error}",
            file=sys.stderr,
        )
        sys.exit(1)

    except errors.APIError as error:
        print(
            f"Gemini API request failed.\n{error}",
            file=sys.stderr,
        )
        sys.exit(1)

    validated_data, error_message = validate_extraction(json_text)

    if validated_data is not None:
        print(validated_data.model_dump_json())
        break

    validation_error = error_message

    print(
        f"Attempt {attempt} failed validation.\n{error_message}",
        file=sys.stderr,
    )

else:
    print(
        f"Extraction failed after {MAX_ATTEMPTS} attempts.",
        file=sys.stderr,
    )
    sys.exit(1)