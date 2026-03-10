"""User Profile, Cars, Payment Methods API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import (
    UserProfileResponse, CompleteProfileRequest, UpdateProfileRequest,
    ChangePasswordRequest, CarCreate, CarUpdate, CarResponse,
    PaymentMethodCreate, PaymentMethodResponse
)
from app.core.security import get_current_user, verify_password, get_password_hash
from app.services import get_auth_service, get_car_service, get_payment_method_service

router = APIRouter(prefix="/users", tags=["Users & Profile"])


# ─── Profile ──────────────────────────────────────────

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    auth = get_auth_service()
    user = auth.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        name=user["name"],
        phone=user.get("phone"),
        gender=user.get("gender"),
        address=user.get("address"),
        profile_photo=user.get("profile_photo"),
        role=user["role"],
        is_active=user["is_active"],
        created_at=user.get("created_at")
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(data: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    auth = get_auth_service()
    update_data = data.model_dump(exclude_none=True)

    if "email" in update_data:
        existing = auth.get_user_by_email(update_data["email"])
        if existing and existing["id"] != current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Email already in use")

    if "gender" in update_data:
        update_data["gender"] = update_data["gender"].value

    user = auth.update_profile(current_user["user_id"], update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        name=user["name"],
        phone=user.get("phone"),
        gender=user.get("gender"),
        address=user.get("address"),
        profile_photo=user.get("profile_photo"),
        role=user["role"],
        is_active=user["is_active"],
        created_at=user.get("created_at")
    )


@router.post("/profile/complete", response_model=UserProfileResponse)
async def complete_profile(data: CompleteProfileRequest, current_user: dict = Depends(get_current_user)):
    auth = get_auth_service()
    profile_data = data.model_dump(exclude_none=True)

    if "gender" in profile_data and profile_data["gender"]:
        profile_data["gender"] = profile_data["gender"].value

    user = auth.complete_profile(current_user["user_id"], profile_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        name=user["name"],
        phone=user.get("phone"),
        gender=user.get("gender"),
        address=user.get("address"),
        profile_photo=user.get("profile_photo"),
        role=user["role"],
        is_active=user["is_active"],
        created_at=user.get("created_at")
    )


@router.put("/change-password")
async def change_password(data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    auth = get_auth_service()
    user = auth.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = get_password_hash(data.new_password)
    user["password_hash"] = new_hash

    return {"success": True, "message": "Password changed successfully"}


# ─── Cars ─────────────────────────────────────────────

@router.get("/cars", response_model=List[CarResponse])
async def get_cars(current_user: dict = Depends(get_current_user)):
    return get_car_service().get_user_cars(current_user["user_id"])


@router.post("/cars", response_model=CarResponse)
async def add_car(data: CarCreate, current_user: dict = Depends(get_current_user)):
    car = get_car_service().add_car(current_user["user_id"], data.model_dump())
    if not car:
        raise HTTPException(status_code=404, detail="User not found")
    return car


@router.put("/cars/{car_id}", response_model=CarResponse)
async def update_car(car_id: str, data: CarUpdate, current_user: dict = Depends(get_current_user)):
    car = get_car_service().update_car(current_user["user_id"], car_id, data.model_dump(exclude_none=True))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.delete("/cars/{car_id}")
async def delete_car(car_id: str, current_user: dict = Depends(get_current_user)):
    if not get_car_service().delete_car(current_user["user_id"], car_id):
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "message": "Car removed successfully"}


@router.put("/cars/{car_id}/default", response_model=CarResponse)
async def set_default_car(car_id: str, current_user: dict = Depends(get_current_user)):
    car = get_car_service().set_default_car(current_user["user_id"], car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


# ─── Payment Methods ─────────────────────────────────

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(current_user: dict = Depends(get_current_user)):
    return get_payment_method_service().get_user_methods(current_user["user_id"])


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(data: PaymentMethodCreate, current_user: dict = Depends(get_current_user)):
    pm = get_payment_method_service().add_method(current_user["user_id"], data.model_dump())
    if not pm:
        raise HTTPException(status_code=404, detail="User not found")
    return pm


@router.delete("/payment-methods/{method_id}")
async def delete_payment_method(method_id: str, current_user: dict = Depends(get_current_user)):
    if not get_payment_method_service().delete_method(current_user["user_id"], method_id):
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"success": True, "message": "Payment method removed"}


@router.put("/payment-methods/{method_id}/default", response_model=PaymentMethodResponse)
async def set_default_payment(method_id: str, current_user: dict = Depends(get_current_user)):
    pm = get_payment_method_service().set_default_method(current_user["user_id"], method_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return pm
