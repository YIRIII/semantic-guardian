from app.config import DATA_DIR


def load_rules() -> str:
    path = DATA_DIR / "rules.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


RULES_TEXT = load_rules()
