"""Auth API Routes"""

from fastapi import APIRouter, HTTPException, status
from app.models import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    SocialLoginRequest, ForgotPasswordEmailRequest, ForgotPasswordPhoneRequest,
    VerifyCodeRequest, ResendCodeRequest, ResetPasswordRequest
)
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.services import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    auth = get_auth_service()
    if auth.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = auth.create_user(data.email, data.name, get_password_hash(data.password), data.phone)
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


@router.post("/social", response_model=TokenResponse)
async def social_login(data: SocialLoginRequest):
    """Login or register via social provider (Google, Facebook, Apple)."""
    if data.provider not in ["google", "facebook", "apple"]:
        raise HTTPException(status_code=400, detail="Unsupported provider. Use: google, facebook, apple")

    auth = get_auth_service()
    user = auth.social_login(
        provider=data.provider,
        token=data.token,
        name=data.name,
        email=data.email
    )

    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )


@router.post("/forgot-password/email")
async def forgot_password_email(data: ForgotPasswordEmailRequest):
    """Send password reset code to email."""
    auth = get_auth_service()
    user = auth.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")

    code = auth.generate_reset_code(data.email)

    masked_email = data.email[0] + "****@" + data.email.split("@")[1]

    return {
        "success": True,
        "message": f"Verification code sent to {masked_email}",
        "masked_identifier": masked_email,
        "method": "email",
        # In production, remove this. Included for demo/testing only.
        "demo_code": code
    }


@router.post("/forgot-password/phone")
async def forgot_password_phone(data: ForgotPasswordPhoneRequest):
    """Send password reset code to phone."""
    auth = get_auth_service()
    user = auth.get_user_by_phone(data.phone)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this phone number")

    code = auth.generate_reset_code(data.phone)

    masked_phone = data.phone[:4] + "****" + data.phone[-2:]

    return {
        "success": True,
        "message": f"Verification code sent to {masked_phone}",
        "masked_identifier": masked_phone,
        "method": "phone",
        "demo_code": code
    }


@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest):
    """Verify OTP code sent to email or phone."""
    auth = get_auth_service()
    identifier = data.email or data.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Provide either email or phone")

    if auth.verify_reset_code(identifier, data.code):
        return {"success": True, "message": "Code verified successfully", "verified": True}

    raise HTTPException(status_code=400, detail="Invalid or expired verification code")


@router.post("/resend-code")
async def resend_code(data: ResendCodeRequest):
    """Resend verification code."""
    auth = get_auth_service()
    identifier = data.email or data.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Provide either email or phone")

    if data.email:
        user = auth.get_user_by_email(data.email)
    else:
        user = auth.get_user_by_phone(data.phone)

    if not user:
        raise HTTPException(status_code=404, detail="Account not found")

    code = auth.generate_reset_code(identifier)

    return {
        "success": True,
        "message": "New verification code sent",
        "demo_code": code
    }


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using verification code."""
    auth = get_auth_service()
    identifier = data.email or data.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Provide either email or phone")

    if not auth.verify_reset_code(identifier, data.code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    new_hash = get_password_hash(data.new_password)
    if not auth.reset_password(identifier, new_hash):
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "message": "Password reset successfully"}
