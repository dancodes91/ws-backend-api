"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.routers import auth, dealers, vendors, files, links, wallace, notifications, reports

settings = get_settings()

app = FastAPI(
    title="Price File Distribution API",
    description="Backend API for Wallace Dealer Portal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dealers.router)
app.include_router(vendors.router)
app.include_router(files.router)
app.include_router(links.router)
app.include_router(wallace.router)
app.include_router(notifications.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _ensure_tables_and_seed():
    """Create tables if missing and seed initial admin. Safe to run on every startup."""
    from app import models  # noqa: F401 - register all models with Base.metadata
    from app.models import Admin
    from app.services.auth_service import hash_password

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Admin).first():
            return
        admin = Admin(
            name="Admin",
            email="admin@wallacedms.com",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup():
    from app.utils.storage import ensure_storage_path
    ensure_storage_path()
    _ensure_tables_and_seed()
