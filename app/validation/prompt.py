import json

from app.config import DATA_DIR
from app.validation.rules import RULES_TEXT

_FALLBACK_TEMPLATE = """أنت نظام تحقق دلالي لحظي لجودة بيانات الاستبيانات (Semantic Guardian).
مهمتك: اكتشاف التعارضات المنطقية والدلالية بين الحقول المختلفة في الاستمارة، ثم إرجاع نتيجة منظمة بصيغة JSON فقط.

المطلوب منك:
1) اكتشاف التعارضات بين الحقول (Cross-field consistency).
2) لكل مشكلة: حدّد الحقول المتأثرة، وصف المشكلة بالعربية، الشدة severity، ودرجة ثقة confidence (0..1).
3) أعطِ درجة ثقة عامة overall_trust_score من 0 إلى 1 لجودة الاستمارة ككل.
4) إن كانت البيانات منطقية: issues تكون قائمة فارغة.

شدة المشكلة severity: low / medium / high

قواعد/إرشادات منطقية:
{RULES}

مهم: أرجع JSON فقط بهذه البنية بالضبط:
{{
  "issues": [
    {{ "fields": ["..."], "description_ar": "...", "severity": "low|medium|high", "confidence": 0.0 }}
  ],
  "overall_trust_score": 0.0
}}

السجل:
{ANSWERS_JSON}"""


def _load_template() -> str:
    path = DATA_DIR / "prompt_template.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return _FALLBACK_TEMPLATE


_TEMPLATE = _load_template()


def build_prompt(payload: dict) -> str:
    answers_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return _TEMPLATE.replace("{RULES}", RULES_TEXT).replace("{ANSWERS_JSON}", answers_json)
