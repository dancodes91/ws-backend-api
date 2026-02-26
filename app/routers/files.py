"""File upload and management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models import PriceFile, Vendor
from app.schemas.file import FileUploadResponse, FileResponse as FileResponseSchema, FileList
from app.dependencies import get_current_admin, get_current_dealer, get_current_user_optional, wallace_api_key
from app.services.file_service import create_price_file, get_file_by_id, list_files, delete_price_file
from app.config import get_settings

router = APIRouter(prefix="/api/files", tags=["files"])
settings = get_settings()
MAX_SIZE = settings.max_upload_size_mb * 1024 * 1024


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    vendor_id: int = Form(...),
    dealer_id: int | None = Form(None),
    version: str | None = Form(None),
    uploaded_by: str | None = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    by = uploaded_by or admin.email
    pf = create_price_file(db, vendor_id, dealer_id, file.filename or "file", content, by, version)
    return pf


@router.post("/upload-utility", response_model=FileUploadResponse)
async def upload_file_from_utility(
    file: UploadFile = File(...),
    vendor_code: str = Form(...),
    dealer_id: int | None = Form(None),
    custom_folder: str | None = Form(None),
    db: Session = Depends(get_db),
    _api_key=Depends(wallace_api_key),
):
    """Used by Wallace PC upload utility. Authenticated via X-API-Key."""
    vendor = db.query(Vendor).filter(Vendor.code == vendor_code).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vendor code not found: {vendor_code}")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    pf = create_price_file(
        db, vendor.id, dealer_id, file.filename or "file", content, "wallace_utility", None
    )
    return pf


@router.get("", response_model=list[FileList])
def list_files_route(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    vendor_id: int | None = Query(None),
    dealer_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return list_files(db, vendor_id=vendor_id, dealer_id=dealer_id, skip=skip, limit=limit)


@router.get("/{file_id}", response_model=FileResponseSchema)
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    pf = get_file_by_id(db, file_id)
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return pf


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_route(
    file_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    pf = get_file_by_id(db, file_id)
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    delete_price_file(db, pf)
