"""Auth API Routes"""

from fastapi import APIRouter, HTTPException, status
from app.models import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.services import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    auth = get_auth_service()
    if auth.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = auth.create_user(data.email, data.name, get_password_hash(data.password))
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    auth = get_auth_service()
    user = auth.get_user_by_email(data.email)
    
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    auth = get_auth_service()
    user = auth.get_user_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )
