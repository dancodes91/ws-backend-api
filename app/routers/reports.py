"""Reports and activity logs."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import AuditLog, DownloadLink, PriceFile
from app.schemas.audit import AuditLogResponse
from app.dependencies import get_current_admin

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/downloads")
def download_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Download statistics: count by file, by dealer, etc."""
    total = db.query(DownloadLink).filter(DownloadLink.downloaded_at != None).count()
    by_dealer = (
        db.query(DownloadLink.dealer_id, func.count(DownloadLink.id).label("count"))
        .filter(DownloadLink.downloaded_at != None)
        .group_by(DownloadLink.dealer_id)
        .all()
    )
    return {"total_downloads": total, "by_dealer": [{"dealer_id": d, "count": c} for d, c in by_dealer]}


@router.get("/activity", response_model=list[AuditLogResponse])
def activity_logs(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
