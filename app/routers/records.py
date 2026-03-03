import json

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmployeeRecord

router = APIRouter(prefix="/records")

PAGE_SIZE = 15


@router.get("")
async def records_list(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query("", alias="q"),
    filter_valid: str = Query("all", alias="filter"),
    db: Session = Depends(get_db),
):
    query = db.query(EmployeeRecord)

    if search:
        query = query.filter(
            (EmployeeRecord.record_id.contains(search))
            | (EmployeeRecord.job_title.contains(search))
        )
    if filter_valid == "valid":
        query = query.filter(EmployeeRecord.is_valid == True)
    elif filter_valid == "invalid":
        query = query.filter(EmployeeRecord.is_valid == False)

    total = query.count()
    total_pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    records = query.order_by(EmployeeRecord.id).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

    return request.app.state.templates.TemplateResponse(
        "records/list.html",
        {
            "request": request,
            "records": records,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "filter_valid": filter_valid,
        },
    )


@router.get("/add")
async def add_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        "records/add_form.html",
        {"request": request},
    )


@router.get("/{record_db_id}")
async def record_detail(record_db_id: int, request: Request, db: Session = Depends(get_db)):
    record = db.query(EmployeeRecord).filter(EmployeeRecord.id == record_db_id).first()
    if not record:
        return request.app.state.templates.TemplateResponse(
            "records/detail.html",
            {"request": request, "record": None, "issues": []},
        )

    issues = []
    for iss in record.issues:
        issues.append({
            "fields": json.loads(iss.fields) if iss.fields else [],
            "description_ar": iss.description_ar,
            "severity": iss.severity,
            "confidence": iss.confidence,
        })

    return request.app.state.templates.TemplateResponse(
        "records/detail.html",
        {"request": request, "record": record, "issues": issues},
    )
