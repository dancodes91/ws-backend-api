"""Notification routes (upload notifications from utility)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import wallace_api_key
from app.services.email_service import send_upload_notification_email

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class UploadNotificationBody(BaseModel):
    vendor: str
    dealer_name: str
    filename: str
    notification_emails: list[str]


@router.post("/upload")
def upload_notification(
    data: UploadNotificationBody,
    db: Session = Depends(get_db),
    _api_key=Depends(wallace_api_key),
):
    """Called by Wallace upload utility after a file is uploaded. Sends email to Jack/Tom."""
    send_upload_notification_email(
        data.notification_emails,
        data.vendor,
        data.dealer_name,
        data.filename,
    )
    return {"status": "ok"}
