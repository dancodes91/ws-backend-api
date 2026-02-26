"""Audit log schemas."""
from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    user_type: str | None
    action: str
    details: str | None
    ip_address: str | None
    timestamp: datetime

    class Config:
        from_attributes = True
