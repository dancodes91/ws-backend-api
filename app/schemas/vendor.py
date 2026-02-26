"""Vendor schemas."""
from datetime import datetime
from pydantic import BaseModel


class VendorCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class VendorUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class VendorResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True
