import json
import logging

from google import genai

from app.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None and GOOGLE_API_KEY:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def _parse_json(text: str) -> dict | list:
    """Try parsing raw JSON, then extract JSON from markdown fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from first { to last } or [ to ]
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Cannot parse JSON from model output: {text[:300]}")


async def call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """Call Gemini and return parsed JSON response."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Gemini client not configured (missing GOOGLE_API_KEY)")

    resp = client.models.generate_content(model=model, contents=prompt)
    text = (resp.text or "").strip()
    return _parse_json(text)
