"""FastAPI dependencies: auth, db, rate limit."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dealer, Admin
from app.utils.security import decode_token
from app.services.auth_service import validate_refresh_token

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Dealer | Admin | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("token_kind") == "refresh":
        return None
    if payload.get("type") not in ("dealer", "admin"):
        return None
    user_id = payload.get("id")
    user_type = payload.get("type")
    if user_type == "dealer":
        return db.get(Dealer, user_id)
    return db.get(Admin, user_id)


def get_current_user(
    user: Dealer | Admin | None = Depends(get_current_user_optional),
) -> Dealer | Admin:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(user, Dealer) and not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return user


def get_current_admin(
    user: Dealer | Admin = Depends(get_current_user),
) -> Admin:
    if not isinstance(user, Admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_current_dealer(
    user: Dealer | Admin = Depends(get_current_user),
) -> Dealer:
    if not isinstance(user, Dealer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dealer access required")
    return user


def wallace_api_key(api_key: str | None = Depends(api_key_header)):
    from app.config import get_settings
    if api_key != get_settings().wallace_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key
