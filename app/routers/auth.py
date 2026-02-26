"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dealer, Admin
from app.schemas.auth import LoginRequest, Token, RefreshRequest
from app.services.auth_service import (
    authenticate_dealer,
    authenticate_admin,
    create_tokens_for_dealer,
    create_tokens_for_admin,
    validate_refresh_token,
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
