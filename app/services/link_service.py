"""Download link generation and validation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import DownloadLink, PriceFile, Dealer
from app.utils.security import create_download_token
from app.utils.storage import get_full_path
from app.config import get_settings

settings = get_settings()


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware (for DB comparison and storage)."""
    return datetime.now(timezone.utc)


def generate_links(db: Session, dealer_id: int, file_ids: list[int], base_url: str) -> list[DownloadLink]:
    """Generate secure download links for given dealer and files."""
    dealer = db.get(Dealer, dealer_id)
    if not dealer or not dealer.active:
        raise ValueError("Dealer not found or inactive")
    links_created = []
    expires_at = _utc_now() + timedelta(days=settings.download_link_expire_days)
    for file_id in file_ids:
        pf = db.get(PriceFile, file_id)
        if not pf:
            continue
        if pf.dealer_id and pf.dealer_id != dealer_id:
            continue
        token = create_download_token()
        link = DownloadLink(
            file_id=file_id,
            dealer_id=dealer_id,
            token=token,
            expires_at=expires_at,
        )
        db.add(link)
        links_created.append((link, pf))
    db.commit()
    for link in links_created:
        db.refresh(link[0])
    return [l[0] for l in links_created]


def get_link_by_token(db: Session, token: str) -> tuple[DownloadLink, PriceFile] | None:
    """Validate token and return (link, price_file) or None."""
    link = db.query(DownloadLink).filter(DownloadLink.token == token).first()
    if not link:
        return None
    # Compare with timezone-aware UTC now (DB returns aware datetimes for DateTime(timezone=True))
    if link.expires_at < _utc_now():
        return None
    pf = db.get(PriceFile, link.file_id)
    if not pf:
        return None
    return link, pf


def mark_downloaded(db: Session, link: DownloadLink) -> None:
    if link.downloaded_at is None:
        link.downloaded_at = _utc_now()
        db.commit()


def get_file_content(link: DownloadLink, price_file: PriceFile) -> tuple[Path, str]:
    """Return (full_path, filename) for streaming download."""
    path = get_full_path(price_file.file_path)
    return path, price_file.filename


def get_dealer_by_customer_number(db: Session, customer_number: str) -> Dealer | None:
    return db.query(Dealer).filter(Dealer.customer_number == customer_number, Dealer.active == True).first()
