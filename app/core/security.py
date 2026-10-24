from fastapi import Header, HTTPException
from app.core.config import settings


def require_admin(x_admin_key: str = Header(...)) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="admin authorization required")
