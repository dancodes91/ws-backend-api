"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import httpx
from urllib.parse import urlencode
from app.database import get_db
from app.models import Dealer, Admin, AuditLog
from app.schemas.auth import (
    LoginRequest,
    Token,
    RefreshRequest,
    DealerRegisterRequest,
    DealerRegisterResponse,
)
from app.services.auth_service import (
    authenticate_dealer,
    authenticate_admin,
    create_tokens_for_dealer,
    create_tokens_for_admin,
    validate_refresh_token,
    hash_password,
)
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login as dealer or admin. Try admin first, then dealer."""
    user = authenticate_admin(db, data.email, data.password)
    if user:
        access, refresh = create_tokens_for_admin(user)
        return Token(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    user = authenticate_dealer(db, data.email, data.password)
    if user:
        access, refresh = create_tokens_for_dealer(user)
        return Token(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token."""
    payload = validate_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_type = payload.get("type")
    user_id = payload.get("id")
    sub = payload.get("sub")
    if user_type == "admin":
        admin = db.get(Admin, user_id)
        if not admin or admin.email != sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        access, ref = create_tokens_for_admin(admin)
    else:
        dealer = db.get(Dealer, user_id)
        if not dealer or dealer.email != sub or not dealer.active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        access, ref = create_tokens_for_dealer(dealer)
    return Token(
        access_token=access,
        refresh_token=ref,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/register-dealer",
    response_model=DealerRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_dealer(
    body: DealerRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Public endpoint for dealers to request an account. Creates an inactive dealer pending admin approval."""
    # Basic uniqueness checks
    existing_email = db.query(Dealer).filter(Dealer.email == body.email).first()
    existing_customer = (
        db.query(Dealer).filter(Dealer.customer_number == body.customer_number).first()
    )
    if existing_email or existing_customer:
        # Do not reveal which field conflicts to avoid user enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A dealer with this email or customer number already exists.",
        )

    dealer = Dealer(
        name=body.name,
        email=body.email,
        customer_number=body.customer_number,
        password_hash=hash_password(body.password),
        active=False,
    )
    db.add(dealer)
    db.flush()  # get dealer.id before creating audit log

    ip = request.client.host if request.client else None
    details_parts = []
    details_parts.append(f"customer_number={body.customer_number}")
    if body.notes:
        details_parts.append(f"notes={body.notes}")
    details = "; ".join(details_parts) if details_parts else None

    audit = AuditLog(
        user_id=dealer.id,
        user_type="dealer",
        action="dealer_register_request",
        details=details,
        ip_address=ip,
    )
    db.add(audit)
    db.commit()

    return DealerRegisterResponse(
        message="Registration received. An admin will review and activate your account."
    )


@router.get("/google/login")
def google_login(request: Request):
    """Redirect to Google OAuth 2.0 authorization endpoint."""
    client_id = settings.google_client_id
    if not client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login not configured")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/google/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"auth_url": url}


@router.get("/google/callback")
def google_callback(code: str | None = None, request: Request = None, db: Session = Depends(get_db)):
    """Handle Google OAuth callback: exchange code, verify ID token, issue our JWTs, and redirect to frontend."""
    if code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")

    client_id = settings.google_client_id
    client_secret = settings.google_client_secret
    if not client_id or not client_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login not configured")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/google/callback"

    # Exchange code for tokens
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=10.0) as client:
        token_res = client.post("https://oauth2.googleapis.com/token", data=token_data)
        if token_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code with Google")
        token_json = token_res.json()
        id_token = token_json.get("id_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing id_token from Google")

        # Validate id_token via tokeninfo
        info_res = client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token})
        if info_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id_token from Google")
        info = info_res.json()

    email = info.get("email")
    aud = info.get("aud")
    if not email or aud != client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google token payload")

    # Optional domain restriction
    allowed_domains = [d.strip() for d in settings.google_allowed_domains.split(",") if d.strip()]
    if allowed_domains:
        domain = email.split("@")[-1]
        if domain not in allowed_domains:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email domain is not allowed")

    # Map email to Admin or Dealer
    user = db.query(Admin).filter(Admin.email == email).first()
    if user:
        access, refresh = create_tokens_for_admin(user)
    else:
        dealer = db.query(Dealer).filter(Dealer.email == email, Dealer.active == True).first()  # type: ignore[comparison-overlap]
        if not dealer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No matching active user for this Google account")
        access, refresh = create_tokens_for_dealer(dealer)

    # Redirect back to frontend callback with tokens in fragment so they don't go to server logs
    frontend_base = request.headers.get("X-Frontend-URL") or settings.cors_origins_list[0]
    redirect_target = f"{frontend_base.rstrip('/')}/auth/google/callback#access_token={access}&refresh_token={refresh}"

    html = f"""
<!DOCTYPE html>
<html>
  <head><meta charset="utf-8"><title>Signing in…</title></head>
  <body>
    <script>
      window.location.href = {redirect_target!r};
    </script>
  </body>
</html>
"""
    from fastapi.responses import HTMLResponse

    return HTMLResponse(content=html)
