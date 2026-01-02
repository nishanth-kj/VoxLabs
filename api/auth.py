
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-VoxLabs-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate API Key.
    In production, check this against a database or environment variable.
    """
    if api_key_header == "ox-secret-key":
        return api_key_header
    
    # For now, we allow requests without keys for local dev, 
    # but in production this would raise 403.
    # raise HTTPException(
    #     status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    # )
    return None
