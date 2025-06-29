from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from src.core.config import settings
from src.core.supabase_client import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_uuid: str = payload.get("uuid")
        
        if email is None or user_id is None or user_uuid is None:
            raise credentials_exception
            
        # Get user from database
        supabase = get_supabase_client()
        response = supabase.from_('users').select('*').eq('uuid', user_uuid).maybe_single().execute()
        
        if not response.data:
            raise credentials_exception
            
        return response.data
        
    except JWTError:
        raise credentials_exception 