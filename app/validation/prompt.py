import json

from app.config import DATA_DIR
from app.validation.rules import RULES_TEXT


def _load_template() -> str:
    path = DATA_DIR / "prompt_template.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


_TEMPLATE = _load_template()


def build_prompt(payload: dict) -> str:
    answers_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return _TEMPLATE.replace("{RULES}", RULES_TEXT).replace("{ANSWERS_JSON}", answers_json)
