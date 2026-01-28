"""Booking API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models import BookingCreate, BookingResponse, ActiveBookingResponse
from app.core.security import get_current_user
from app.services import get_booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse)
async def create_booking(data: BookingCreate, current_user: dict = Depends(get_current_user)):
    try:
        return get_booking_service().create_booking(
            current_user["user_id"],
            {
                "parking_id": data.parking_id,
                "slot_id": data.slot_id,
                "vehicle_plate": data.vehicle_plate,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "payment_method": data.payment_method
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[BookingResponse])
async def get_bookings(current_user: dict = Depends(get_current_user)):
    return get_booking_service().get_user_bookings(current_user["user_id"])


@router.get("/active", response_model=Optional[ActiveBookingResponse])
async def get_active(current_user: dict = Depends(get_current_user)):
    return get_booking_service().get_active_booking(current_user["user_id"])


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    for b in get_booking_service().get_user_bookings(current_user["user_id"]):
        if b["id"] == booking_id:
            return b
    raise HTTPException(status_code=404, detail="Booking not found")


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel(booking_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return get_booking_service().cancel_booking(booking_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
