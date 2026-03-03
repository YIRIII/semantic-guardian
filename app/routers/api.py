import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import TRUST_THRESHOLD
from app.database import get_db
from app.models import EmployeeRecord, ValidationIssue
from app.services.stats_service import (
    get_kpis,
    get_trust_distribution,
    get_valid_invalid_chart,
)
from app.services.upload_service import process_upload
from app.validation.engine import validate_record

router = APIRouter(prefix="/api")


@router.post("/upload")
async def api_upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    batch = await process_upload(db, content, file.filename or "upload.xlsx")
    return request.app.state.templates.TemplateResponse(
        "partials/validation_result.html",
        {"request": request, "batch": batch, "total": batch.total_records},
    )


@router.post("/records")
async def api_add_record(
    request: Request,
    age: int = Form(...),
    gender: str = Form(""),
    education_level: str = Form(""),
    job_title: str = Form(""),
    years_of_experience: int = Form(0),
    weekly_working_hours: int = Form(40),
    employment_type: str = Form("دوام كامل"),
    monthly_income: str = Form(""),
    db: Session = Depends(get_db),
):
    payload = {
        "age": age,
        "gender": gender,
        "education_level": education_level,
        "job_title": job_title,
        "years_of_experience": years_of_experience,
        "weekly_working_hours": weekly_working_hours,
        "employment_type": employment_type,
        "monthly_income": monthly_income,
    }

    result, method = await validate_record(payload)
    trust = float(result.get("overall_trust_score", 0))
    issues_data = result.get("issues", [])

    # Generate next record_id
    last = db.query(EmployeeRecord).order_by(EmployeeRecord.id.desc()).first()
    next_num = (last.id if last else 0) + 1
    record_id = f"M{next_num:03d}"

    rec = EmployeeRecord(
        record_id=record_id,
        age=age,
        gender=gender,
        education_level=education_level,
        job_title=job_title,
        years_of_experience=years_of_experience,
        weekly_working_hours=weekly_working_hours,
        employment_type=employment_type,
        monthly_income=monthly_income,
        trust_score=trust,
        is_valid=trust >= TRUST_THRESHOLD,
        issues_count=len(issues_data),
        validation_method=method,
        validated_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    for iss in issues_data:
        db.add(ValidationIssue(
            record_id=rec.id,
            fields=json.dumps(iss.get("fields", []), ensure_ascii=False),
            description_ar=iss.get("description_ar", ""),
            severity=iss.get("severity", "medium"),
            confidence=float(iss.get("confidence", 0)),
        ))
    db.commit()

    return request.app.state.templates.TemplateResponse(
        "partials/validation_result.html",
        {
            "request": request,
            "record": rec,
            "issues": issues_data,
            "trust": trust,
            "method": method,
        },
    )


@router.post("/records/{record_db_id}/revalidate")
async def api_revalidate(
    record_db_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    rec = db.query(EmployeeRecord).filter(EmployeeRecord.id == record_db_id).first()
    if not rec:
        return {"error": "not found"}

    payload = {
        "age": rec.age,
        "gender": rec.gender,
        "education_level": rec.education_level,
        "job_title": rec.job_title,
        "years_of_experience": rec.years_of_experience,
        "weekly_working_hours": rec.weekly_working_hours,
        "employment_type": rec.employment_type,
        "monthly_income": rec.monthly_income,
    }

    result, method = await validate_record(payload)
    trust = float(result.get("overall_trust_score", 0))
    issues_data = result.get("issues", [])

    # Update record
    rec.trust_score = trust
    rec.is_valid = trust >= TRUST_THRESHOLD
    rec.issues_count = len(issues_data)
    rec.validation_method = method
    rec.validated_at = datetime.now(timezone.utc)

    # Replace issues
    for old_iss in rec.issues:
        db.delete(old_iss)
    db.commit()

    for iss in issues_data:
        db.add(ValidationIssue(
            record_id=rec.id,
            fields=json.dumps(iss.get("fields", []), ensure_ascii=False),
            description_ar=iss.get("description_ar", ""),
            severity=iss.get("severity", "medium"),
            confidence=float(iss.get("confidence", 0)),
        ))
    db.commit()

    return request.app.state.templates.TemplateResponse(
        "partials/validation_result.html",
        {
            "request": request,
            "record": rec,
            "issues": issues_data,
            "trust": trust,
            "method": method,
        },
    )


@router.get("/stats")
async def api_stats(db: Session = Depends(get_db)):
    return get_kpis(db)


@router.get("/charts/trust-distribution")
async def api_trust_distribution(db: Session = Depends(get_db)):
    return get_trust_distribution(db)


@router.get("/charts/valid-invalid")
async def api_valid_invalid(db: Session = Depends(get_db)):
    return get_valid_invalid_chart(db)


@router.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    records = db.query(EmployeeRecord).order_by(EmployeeRecord.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "record_id", "age", "gender", "education_level", "job_title",
        "years_of_experience", "weekly_working_hours", "employment_type",
        "monthly_income", "trust_score", "is_valid", "issues_count",
        "validation_method",
    ])
    for r in records:
        writer.writerow([
            r.record_id, r.age, r.gender, r.education_level, r.job_title,
            r.years_of_experience, r.weekly_working_hours, r.employment_type,
            r.monthly_income, r.trust_score, r.is_valid, r.issues_count,
            r.validation_method,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=semantic_guardian_export.csv"},
    )
