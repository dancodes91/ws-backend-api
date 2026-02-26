"""Download link schemas."""
from datetime import datetime
from pydantic import BaseModel


class LinkGenerateRequest(BaseModel):
    dealer_id: int
    file_ids: list[int]  # one or more files


class LinkResponse(BaseModel):
    id: int
    file_id: int
    dealer_id: int
    token: str
    expires_at: datetime
    created_at: datetime
    downloaded_at: datetime | None
    download_url: str | None = None

    class Config:
        from_attributes = True


class LinkDownloadResponse(BaseModel):
    filename: str
    file_path: str
    content_type: str = "application/octet-stream"


class WallaceGetLinksRequest(BaseModel):
    customer_number: str
    vendors: list[str]  # e.g. ["KEL_SILV", "YAMAHA", "MERCURY"]


class WallaceLinkItem(BaseModel):
    vendor: str
    link: str
    filename: str
    expires_at: datetime


class WallaceGetLinksResponse(BaseModel):
    links: list[WallaceLinkItem]
    dealer_email: str
