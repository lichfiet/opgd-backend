import os

from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if (api_key_env := os.getenv("ADMIN_API_KEY")) and api_key == api_key_env:
        return
    raise HTTPException(status_code=403, detail="Invalid API Key")