import pandas as pd

COL_MAP_CANDIDATES = {
    "record_id": ["record_id", "RecordID", "id", "ID", "رقم_السجل", "رقم السجل"],
    "age": ["age", "Age", "العمر"],
    "gender": ["gender", "Gender", "sex", "Sex", "الجنس", "نوع الجنس"],
    "education_level": ["education_level", "Education", "education", "المؤهل", "المستوى التعليمي"],
    "job_title": ["job_title", "JobTitle", "job", "المسمى الوظيفي", "المسمى"],
    "years_of_experience": ["years_of_experience", "experience_years", "exp_years", "سنوات الخبرة", "الخبرة"],
    "weekly_working_hours": ["weekly_working_hours", "hours_per_week", "ساعات العمل الأسبوعية", "ساعات_اسبوعية"],
    "employment_type": ["employment_type", "employment", "نوع التوظيف", "نوع العمل"],
    "monthly_income": ["monthly_income", "income", "الدخل الشهري", "الراتب"],
}


def pick_col(columns: list[str], target: str) -> str | None:
    """Find the actual column name in `columns` matching a canonical target."""
    candidates = COL_MAP_CANDIDATES.get(target, [])
    for name in candidates:
        if name in columns:
            return name
    return None


def resolve_columns(columns: list[str]) -> dict[str, str | None]:
    """Resolve all canonical column names to actual column names."""
    columns = [c.strip() for c in columns]
    return {target: pick_col(columns, target) for target in COL_MAP_CANDIDATES}


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names and return normalized DataFrame."""
    df.columns = [c.strip() for c in df.columns]
    resolved = resolve_columns(list(df.columns))
    rename_map = {v: k for k, v in resolved.items() if v is not None and v != k}
    return df.rename(columns=rename_map)
