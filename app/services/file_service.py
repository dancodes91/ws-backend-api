"""File upload and storage service."""
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import PriceFile, Vendor, Dealer
from app.utils.storage import save_upload_file, ensure_storage_path
from app.config import get_settings

settings = get_settings()


def get_vendor_by_code(db: Session, code: str) -> Vendor | None:
    return db.query(Vendor).filter(Vendor.code == code).first()


def create_price_file(
    db: Session,
    vendor_id: int,
    dealer_id: int | None,
    filename: str,
    file_content: bytes,
    uploaded_by: str,
    version: str | None = None,
) -> PriceFile:
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    vendor_code = vendor.code
    relative_path = save_upload_file(file_content, vendor_code, dealer_id, filename)
    pf = PriceFile(
        vendor_id=vendor_id,
        dealer_id=dealer_id,
        filename=filename,
        file_path=relative_path,
        version=version,
        uploaded_by=uploaded_by,
    )
    db.add(pf)
    db.commit()
    db.refresh(pf)
    return pf


def get_file_by_id(db: Session, file_id: int) -> PriceFile | None:
    return db.query(PriceFile).filter(PriceFile.id == file_id).first()


def list_files(
    db: Session,
    vendor_id: int | None = None,
    dealer_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PriceFile]:
    q = db.query(PriceFile)
    if vendor_id is not None:
        q = q.filter(PriceFile.vendor_id == vendor_id)
    if dealer_id is not None:
        q = q.filter(PriceFile.dealer_id == dealer_id)
    return q.order_by(PriceFile.uploaded_at.desc()).offset(skip).limit(limit).all()


def delete_price_file(db: Session, pf: PriceFile) -> bool:
    from app.utils.storage import delete_file
    delete_file(pf.file_path)
    db.delete(pf)
    db.commit()
    return True
