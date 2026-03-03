import asyncio
import json
import logging

from app.validation.prompt import build_prompt
from app.validation.gemini import call_gemini
from app.validation.offline import offline_checks
from app.validation.rules import RULES_TEXT

logger = logging.getLogger(__name__)

# Track whether Gemini is available this session to avoid repeated failures
_gemini_available = True


def reset_gemini_status():
    global _gemini_available
    _gemini_available = True


async def validate_record(payload: dict) -> tuple[dict, str]:
    """Validate a single employee record.
    Tries Gemini once; if it fails, falls back to offline immediately.
    """
    global _gemini_available

    if _gemini_available:
        try:
            prompt = build_prompt(payload)
            result = await call_gemini(prompt)
            return result, "gemini"
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Gemini quota exceeded — switching to offline for this session")
                _gemini_available = False
            else:
                logger.error(f"Gemini error: {e}")

    return offline_checks(payload), "offline"


async def validate_batch_records(payloads: list[dict]) -> list[tuple[dict, str]]:
    """Validate a list of records. Tries Gemini batch once, falls back to offline.

    Each payload dict should have record_id + employee fields.
    Returns list of (result_dict, method).
    """
    global _gemini_available

    if _gemini_available:
        try:
            batch_prompt = _build_batch_prompt(payloads)
            results = await call_gemini(batch_prompt)
            if isinstance(results, list):
                # Map results by record_id for alignment
                result_map = {r.get("record_id"): r for r in results}
                out = []
                for p in payloads:
                    rid = p.get("record_id", "")
                    if rid in result_map:
                        out.append((result_map[rid], "gemini"))
                    else:
                        out.append((offline_checks(p), "offline"))
                return out
        except Exception as e:
            if "429" in str(e):
                logger.warning("Gemini quota exceeded on batch — switching to offline")
                _gemini_available = False
            else:
                logger.error(f"Batch Gemini error: {e}")

    # Offline fallback for all
    results = []
    for p in payloads:
        r = offline_checks(p)
        r["record_id"] = p.get("record_id", "")
        results.append((r, "offline"))
    return results


def _build_batch_prompt(payloads: list[dict]) -> str:
    return f"""أنت نظام تحقق دلالي لحظي لجودة بيانات الاستبيانات.
مهمتك: تقييم كل سجل وإرجاع JSON فقط (بدون أي شرح أو Markdown).

ارجع النتيجة EXACTLY بهذا الشكل (قائمة):
[
  {{
    "record_id": "R001",
    "issues": [
      {{"fields":["..."], "description_ar":"...", "severity":"low|medium|high", "confidence":0.0}}
    ],
    "overall_trust_score": 0.0
  }}
]

القواعد:
{RULES_TEXT}

السجلات:
{json.dumps(payloads, ensure_ascii=False, indent=2)}
"""
