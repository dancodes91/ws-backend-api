"""Vendor CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.dependencies import get_current_admin

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorResponse])
def list_vendors(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    return db.query(Vendor).order_by(Vendor.code).offset(skip).limit(limit).all()


@router.post("", response_model=VendorResponse)
def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    if db.query(Vendor).filter(Vendor.code == data.code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor code already exists")
    vendor = Vendor(code=data.code, name=data.name, description=data.description)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if data.code is not None:
        if db.query(Vendor).filter(Vendor.code == data.code, Vendor.id != vendor_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor code already in use")
        vendor.code = data.code
    if data.name is not None:
        vendor.name = data.name
    if data.description is not None:
        vendor.description = data.description
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
