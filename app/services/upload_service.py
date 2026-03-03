import json
import logging
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from app.config import TRUST_THRESHOLD
from app.models import EmployeeRecord, UploadBatch, ValidationIssue
from app.utils.columns import normalize_dataframe
from app.validation.engine import validate_batch_records, validate_record

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


def parse_file(content: bytes, filename: str) -> pd.DataFrame:
    """Parse Excel or CSV file bytes into a normalized DataFrame."""
    buf = BytesIO(content)
    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(buf)
    else:
        df = pd.read_csv(buf)
    return normalize_dataframe(df)


def _make_record_id(index: int) -> str:
    return f"R{index + 1:03d}"


async def process_upload(db: Session, content: bytes, filename: str) -> UploadBatch:
    """Parse file, create batch, validate all records, persist results."""
    df = parse_file(content, filename)

    batch = UploadBatch(
        filename=filename,
        total_records=len(df),
        status="processing",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Build all payloads first
    payloads = []
    for idx, row in df.iterrows():
        rid = row.get("record_id", _make_record_id(idx))
        payload = _row_to_payload(row)
        payload["record_id"] = str(rid)
        payloads.append(payload)

    # Validate in batches
    all_results = []
    for i in range(0, len(payloads), BATCH_SIZE):
        chunk = payloads[i : i + BATCH_SIZE]
        results = await validate_batch_records(chunk)
        all_results.extend(results)

    # Persist all records
    for payload, (result, method) in zip(payloads, all_results):
        trust = float(result.get("overall_trust_score", 0))
        issues_data = result.get("issues", [])

        rec = EmployeeRecord(
            batch_id=batch.id,
            record_id=payload["record_id"],
            age=payload.get("age"),
            gender=payload.get("gender"),
            education_level=payload.get("education_level"),
            job_title=payload.get("job_title"),
            years_of_experience=payload.get("years_of_experience"),
            weekly_working_hours=payload.get("weekly_working_hours"),
            employment_type=payload.get("employment_type"),
            monthly_income=payload.get("monthly_income"),
            trust_score=trust,
            is_valid=trust >= TRUST_THRESHOLD,
            issues_count=len(issues_data),
            validation_method=method,
            validated_at=datetime.now(timezone.utc),
        )
        db.add(rec)
        db.flush()

        for iss in issues_data:
            db.add(ValidationIssue(
                record_id=rec.id,
                fields=json.dumps(iss.get("fields", []), ensure_ascii=False),
                description_ar=iss.get("description_ar", ""),
                severity=iss.get("severity", "medium"),
                confidence=float(iss.get("confidence", 0)),
            ))

    batch.status = "completed"
    db.commit()
    db.refresh(batch)
    return batch


def _row_to_payload(row) -> dict:
    """Convert a DataFrame row to a validation payload dict."""
    def safe_int(v):
        try:
            if pd.notna(v):
                return int(v)
        except (ValueError, TypeError):
            pass
        return None

    return {
        "age": safe_int(row.get("age")),
        "gender": str(row.get("gender", "")) if pd.notna(row.get("gender")) else "",
        "education_level": str(row.get("education_level", "")) if pd.notna(row.get("education_level")) else "",
        "job_title": str(row.get("job_title", "")) if pd.notna(row.get("job_title")) else "",
        "years_of_experience": safe_int(row.get("years_of_experience")),
        "weekly_working_hours": safe_int(row.get("weekly_working_hours")),
        "employment_type": str(row.get("employment_type", "")) if pd.notna(row.get("employment_type")) else "",
        "monthly_income": str(row.get("monthly_income", "")) if pd.notna(row.get("monthly_income")) else "",
    }
