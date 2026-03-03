from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, TEMPLATES_DIR
from app.database import init_db
from app.routers import api, dashboard, records, upload

app = FastAPI(title="الحارس الدلالي - Semantic Guardian")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(dashboard.router)
app.include_router(records.router)
app.include_router(upload.router)
app.include_router(api.router)


@app.on_event("startup")
def on_startup():
    init_db()
