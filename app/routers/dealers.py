"""Dealer CRUD routes (admin only)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.config import get_settings
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dealer, DealerVendor, Vendor
from app.schemas.dealer import DealerCreate, DealerUpdate, DealerResponse, DealerList, DealerVendorSchema
from app.dependencies import get_current_admin
from app.services.auth_service import hash_password
from app.services.email_service import send_welcome_email

router = APIRouter(prefix="/api/dealers", tags=["dealers"])
_settings = get_settings()


@router.get("", response_model=list[DealerList])
def list_dealers(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active: bool | None = None,
):
    q = db.query(Dealer)
    if active is not None:
        q = q.filter(Dealer.active == active)
    return q.order_by(Dealer.name).offset(skip).limit(limit).all()


@router.post("", response_model=DealerResponse)
def create_dealer(
    data: DealerCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    if db.query(Dealer).filter(Dealer.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if db.query(Dealer).filter(Dealer.customer_number == data.customer_number).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer number already exists")
    dealer = Dealer(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        customer_number=data.customer_number,
        active=data.active,
    )
    db.add(dealer)
    db.commit()
    db.refresh(dealer)
    send_welcome_email(dealer.email, dealer.name, "https://portal.wallacedms.com/login")
    return dealer


@router.get("/{dealer_id}", response_model=DealerResponse)
def get_dealer(
    dealer_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dealer = db.get(Dealer, dealer_id)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found")
    return dealer


@router.put("/{dealer_id}", response_model=DealerResponse)
def update_dealer(
    dealer_id: int,
    data: DealerUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dealer = db.get(Dealer, dealer_id)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found")
    if data.name is not None:
        dealer.name = data.name
    if data.email is not None:
        if db.query(Dealer).filter(Dealer.email == data.email, Dealer.id != dealer_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        dealer.email = data.email
    if data.password is not None:
        dealer.password_hash = hash_password(data.password)
    if data.customer_number is not None:
        if db.query(Dealer).filter(Dealer.customer_number == data.customer_number, Dealer.id != dealer_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer number already in use")
        dealer.customer_number = data.customer_number
    if data.active is not None:
        dealer.active = data.active
    db.commit()
    db.refresh(dealer)
    return dealer


@router.delete("/{dealer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dealer(
    dealer_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dealer = db.get(Dealer, dealer_id)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found")
    db.delete(dealer)
    db.commit()


@router.get("/{dealer_id}/vendors")
def get_dealer_vendors(
    dealer_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dealer = db.get(Dealer, dealer_id)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found")
    return [
        {"vendor_id": dv.vendor_id, "custom_folder_name": dv.custom_folder_name, "vendor_code": dv.vendor.code}
        for dv in dealer.vendors
    ]


@router.post("/{dealer_id}/vendors")
def assign_dealer_vendors(
    dealer_id: int,
    vendors: list[DealerVendorSchema],
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dealer = db.get(Dealer, dealer_id)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found")
    # Replace existing
    db.query(DealerVendor).filter(DealerVendor.dealer_id == dealer_id).delete()
    for v in vendors:
        vendor = db.get(Vendor, v.vendor_id)
        if not vendor:
            continue
        dv = DealerVendor(dealer_id=dealer_id, vendor_id=v.vendor_id, custom_folder_name=v.custom_folder_name)
        db.add(dv)
    db.commit()
    return {"status": "ok"}
