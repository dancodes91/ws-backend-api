"""Wallace integration API: get links by customer number and vendor codes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dealer, DealerVendor, Vendor, PriceFile, DownloadLink
from app.schemas.link import WallaceGetLinksRequest, WallaceGetLinksResponse, WallaceLinkItem
from app.dependencies import wallace_api_key
from app.services.link_service import generate_links, get_dealer_by_customer_number
from app.config import get_settings

router = APIRouter(prefix="/api/wallace", tags=["wallace"])
settings = get_settings()


@router.post("/get-links", response_model=WallaceGetLinksResponse)
def get_links_for_wallace(
    data: WallaceGetLinksRequest,
    request: Request,
    db: Session = Depends(get_db),
    _api_key=Depends(wallace_api_key),
):
    """
    Wallace calls this when Jack charges a customer for price files.
    Returns secure download links for each vendor. Wallace can then email these to the dealer.
    """
    dealer = get_dealer_by_customer_number(db, data.customer_number)
    if not dealer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealer not found for customer number")
    # Resolve vendor codes (or custom folder names) to file_ids
    file_ids = []
    for vendor_code in data.vendors:
        vendor = db.query(Vendor).filter(Vendor.code == vendor_code).first()
        if not vendor:
            # Maybe it's a custom_folder_name for this dealer
            dv = db.query(DealerVendor).filter(
                DealerVendor.dealer_id == dealer.id,
                DealerVendor.custom_folder_name == vendor_code,
            ).first()
            if dv:
                vendor = db.get(Vendor, dv.vendor_id)
        if not vendor:
            continue
        # Latest file: dealer-specific first, then shared
        pf = (
            db.query(PriceFile)
            .filter(PriceFile.vendor_id == vendor.id, PriceFile.dealer_id == dealer.id)
            .order_by(PriceFile.uploaded_at.desc())
            .first()
        )
        if not pf:
            pf = (
                db.query(PriceFile)
                .filter(PriceFile.vendor_id == vendor.id, PriceFile.dealer_id == None)
                .order_by(PriceFile.uploaded_at.desc())
                .first()
            )
        if not pf:
            pf = (
                db.query(PriceFile)
                .filter(PriceFile.vendor_id == vendor.id)
                .order_by(PriceFile.uploaded_at.desc())
                .first()
            )
        if pf:
            file_ids.append(pf.id)
    if not file_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No price files found for given vendors")
    # Generate links
    base = str(request.base_url).rstrip("/")
    links = generate_links(db, dealer.id, file_ids, base)
    items = []
    for link in links:
        pf = db.get(PriceFile, link.file_id)
        if pf:
            url = f"{base}/api/links/download/{link.token}"
            items.append(
                WallaceLinkItem(
                    vendor=pf.vendor.code,
                    link=url,
                    filename=pf.filename,
                    expires_at=link.expires_at,
                )
            )
    return WallaceGetLinksResponse(links=items, dealer_email=dealer.email)
