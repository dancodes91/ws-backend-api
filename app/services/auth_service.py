"""Authentication service."""
from sqlalchemy.orm import Session
from app.models import Dealer, Admin
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.config import get_settings

settings = get_settings()


def authenticate_dealer(db: Session, email: str, password: str) -> Dealer | None:
    dealer = db.query(Dealer).filter(Dealer.email == email).first()
    if not dealer or not dealer.active:
        return None
    if not verify_password(password, dealer.password_hash):
        return None
    return dealer


def authenticate_admin(db: Session, email: str, password: str) -> Admin | None:
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin


def create_tokens_for_dealer(dealer: Dealer) -> tuple[str, str]:
    payload = {"sub": dealer.email, "type": "dealer", "id": dealer.id}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return access, refresh


def create_tokens_for_admin(admin: Admin) -> tuple[str, str]:
    payload = {"sub": admin.email, "type": "admin", "id": admin.id}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return access, refresh


def hash_password(password: str) -> str:
    return get_password_hash(password)


def validate_refresh_token(token: str) -> dict | None:
    payload = decode_token(token)
    if not payload or payload.get("token_kind") != "refresh":
        return None
    return payload
