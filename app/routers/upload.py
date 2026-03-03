from fastapi import APIRouter, Depends, Request

from app.database import get_db

router = APIRouter()


@router.get("/upload")
async def upload_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "upload.html",
        {"request": request},
    )
