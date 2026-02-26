"""File storage utilities."""
import os
import shutil
from pathlib import Path
from app.config import get_settings

settings = get_settings()


def ensure_storage_path() -> Path:
    path = Path(settings.storage_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_path(vendor_code: str, dealer_id: int | None, filename: str) -> Path:
    base = ensure_storage_path()
    if dealer_id:
        folder = base / vendor_code / str(dealer_id)
    else:
        folder = base / vendor_code
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


def save_upload_file(file_content: bytes, vendor_code: str, dealer_id: int | None, filename: str) -> str:
    path = get_file_path(vendor_code, dealer_id, filename)
    path.write_bytes(file_content)
    return str(path.relative_to(ensure_storage_path())).replace("\\", "/")


def get_full_path(relative_path: str) -> Path:
    return Path(settings.storage_path) / relative_path


def delete_file(relative_path: str) -> bool:
    path = get_full_path(relative_path)
    if path.exists():
        path.unlink()
        return True
    return False
