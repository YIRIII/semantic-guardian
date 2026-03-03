from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import EmployeeRecord, ValidationIssue


def get_kpis(db: Session) -> dict:
    total = db.query(func.count(EmployeeRecord.id)).scalar() or 0
    valid = db.query(func.count(EmployeeRecord.id)).filter(EmployeeRecord.is_valid == True).scalar() or 0
    invalid = total - valid
    avg_trust = db.query(func.avg(EmployeeRecord.trust_score)).scalar() or 0.0
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "avg_trust": round(float(avg_trust), 3),
    }


def get_trust_distribution(db: Session) -> dict:
    """Return histogram data for trust score distribution."""
    records = db.query(EmployeeRecord.trust_score).all()
    scores = [r[0] for r in records if r[0] is not None]

    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    labels = ["0-0.1", "0.1-0.2", "0.2-0.3", "0.3-0.4", "0.4-0.5",
              "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1.0"]
    counts = [0] * len(labels)
    for s in scores:
        for i in range(len(bins) - 1):
            if bins[i] <= s < bins[i + 1]:
                counts[i] += 1
                break

    return {"labels": labels, "data": counts}


def get_valid_invalid_chart(db: Session) -> dict:
    kpis = get_kpis(db)
    return {
        "labels": ["صالح", "غير صالح"],
        "data": [kpis["valid"], kpis["invalid"]],
    }


def get_top_problematic(db: Session, limit: int = 10) -> list:
    records = (
        db.query(EmployeeRecord)
        .filter(EmployeeRecord.issues_count > 0)
        .order_by(EmployeeRecord.trust_score.asc())
        .limit(limit)
        .all()
    )
    return records
