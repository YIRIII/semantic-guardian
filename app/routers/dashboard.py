from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stats_service import get_kpis, get_top_problematic

router = APIRouter()


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    kpis = get_kpis(db)
    top_problems = get_top_problematic(db)
    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "kpis": kpis, "top_problems": top_problems},
    )
