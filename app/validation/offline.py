def offline_checks(payload: dict) -> dict:
    """Rule-based fallback validation -- no API call needed."""
    issues = []
    age = payload.get("age")
    exp = payload.get("years_of_experience")
    hrs = payload.get("weekly_working_hours")
    emp = payload.get("employment_type", "")
    job = payload.get("job_title", "")
    income = payload.get("monthly_income", "")

    # Rule 1: experience > age - 14
    if age is not None and exp is not None and exp > max(age - 14, 0):
        issues.append({
            "fields": ["age", "years_of_experience"],
            "description_ar": "سنوات الخبرة أعلى من الممكن منطقيًا بالنسبة للعمر",
            "severity": "high",
            "confidence": 0.95,
        })

    # Rule 2: age < 18 with senior/managerial title
    senior_keywords = ["مدير", "مستشار", "رئيس", "طبيب", "استشاري"]
    if age is not None and age < 18 and any(k in job for k in senior_keywords):
        issues.append({
            "fields": ["age", "job_title"],
            "description_ar": "العمر أقل من 18 مع مسمى وظيفي إداري/تخصصي عالي",
            "severity": "high",
            "confidence": 0.9,
        })

    # Rule 3: weekly hours > 72
    if hrs is not None and hrs > 72:
        issues.append({
            "fields": ["weekly_working_hours"],
            "description_ar": "ساعات العمل الأسبوعية أعلى من 72 — غير منطقية غالبًا",
            "severity": "medium",
            "confidence": 0.85,
        })

    # Rule 4: part-time but >= 40 hours
    if emp == "دوام جزئي" and hrs is not None and hrs >= 40:
        issues.append({
            "fields": ["employment_type", "weekly_working_hours"],
            "description_ar": "دوام جزئي مع ساعات عمل تعادل أو تتجاوز الدوام الكامل",
            "severity": "medium",
            "confidence": 0.85,
        })

    # Rule 5: high income with simple/entry title
    try:
        upper = int(income.split("-")[-1])
        simple_keywords = ["سائق", "عامل", "نظافة", "حارس", "مندوب"]
        if upper >= 20000 and any(k in job for k in simple_keywords):
            issues.append({
                "fields": ["monthly_income", "job_title"],
                "description_ar": "دخل شهري مرتفع جدًا مع مسمى وظيفي بسيط",
                "severity": "high",
                "confidence": 0.88,
            })
    except (ValueError, IndexError):
        pass

    trust = max(1.0 - 0.25 * len(issues), 0.05)
    return {"issues": issues, "overall_trust_score": round(trust, 3)}
