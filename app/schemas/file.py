"""File schemas."""
from datetime import datetime
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    vendor_id: int
    dealer_id: int | None
    version: str | None
    uploaded_at: datetime
    uploaded_by: str | None

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    vendor_id: int
    dealer_id: int | None
    version: str | None
    uploaded_at: datetime
    uploaded_by: str | None

    class Config:
        from_attributes = True


class FileList(BaseModel):
    id: int
    filename: str
    vendor_id: int
    dealer_id: int | None
    uploaded_at: datetime
    uploaded_by: str | None

    class Config:
        from_attributes = True
