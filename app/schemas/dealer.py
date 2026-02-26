"""Dealer schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class DealerCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    customer_number: str
    active: bool = True


class DealerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    customer_number: str | None = None
    active: bool | None = None


class DealerVendorSchema(BaseModel):
    vendor_id: int
    custom_folder_name: str | None = None


class DealerResponse(BaseModel):
    id: int
    name: str
    email: str
    customer_number: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DealerList(BaseModel):
    id: int
    name: str
    email: str
    customer_number: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
