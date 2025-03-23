from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Annotated

from backend.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: Annotated[str, Security(API_KEY_HEADER)]) -> str:
    if api_key != settings.WEBHOOK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key 