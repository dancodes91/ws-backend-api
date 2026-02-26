"""Download link generation and download routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.link import LinkGenerateRequest, LinkResponse, WallaceLinkItem
from app.dependencies import get_current_admin, get_current_dealer
from app.services.link_service import (
    generate_links,
    get_link_by_token,
    mark_downloaded,
    get_file_content,
)
from app.config import get_settings

router = APIRouter(prefix="/api/links", tags=["links"])
settings = get_settings()


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.post("/generate", response_model=list[LinkResponse])
def generate_download_links(
    data: LinkGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    base = _base_url(request)
    links = generate_links(db, data.dealer_id, data.file_ids, base)
    result = []
    for link in links:
        url = f"{base}/api/links/download/{link.token}"
        result.append(
            LinkResponse(
                id=link.id,
                file_id=link.file_id,
                dealer_id=link.dealer_id,
                token=link.token,
                expires_at=link.expires_at,
                created_at=link.created_at,
                downloaded_at=link.downloaded_at,
                download_url=url,
            )
        )
    return result


@router.get("/download/{token}")
def download_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    """Public endpoint: validate token and stream file. Used by dealer download utility and browser."""
    pair = get_link_by_token(db, token)
    if not pair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link expired or invalid")
    link, price_file = pair
    path, filename = get_file_content(link, price_file)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")
    mark_downloaded(db, link)
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


@router.get("", response_model=list[LinkResponse])
def list_links(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    dealer_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    from app.models import DownloadLink
    q = db.query(DownloadLink)
    if dealer_id is not None:
        q = q.filter(DownloadLink.dealer_id == dealer_id)
    links = q.order_by(DownloadLink.created_at.desc()).offset(skip).limit(limit).all()
    base = _base_url(request)
    return [
        LinkResponse(
            id=l.id,
            file_id=l.file_id,
            dealer_id=l.dealer_id,
            token=l.token,
            expires_at=l.expires_at,
            created_at=l.created_at,
            downloaded_at=l.downloaded_at,
            download_url=f"{base}/api/links/download/{l.token}",
        )
        for l in links
    ]
