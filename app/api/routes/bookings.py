"""Booking API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models import (
    BookingCreate, BookingResponse, ActiveBookingResponse,
    BookingExtendRequest, BookingQRResponse
)
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


@router.get("/history", response_model=List[BookingResponse])
async def get_history(current_user: dict = Depends(get_current_user)):
    """Get past completed and cancelled bookings."""
    return get_booking_service().get_booking_history(current_user["user_id"])


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    booking = get_booking_service().get_booking_by_id(booking_id)
    if not booking or booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/{booking_id}/qr", response_model=BookingQRResponse)
async def get_booking_qr(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Get QR code data for a booking (used for gate entry/exit)."""
    qr = get_booking_service().get_booking_qr(booking_id, current_user["user_id"])
    if not qr:
        raise HTTPException(status_code=404, detail="Booking not found")
    return qr


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel(booking_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return get_booking_service().cancel_booking(booking_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id}/check-in", response_model=BookingResponse)
async def check_in(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Check in to parking (e.g., scan QR at gate). Moves booking from confirmed → active."""
    booking = get_booking_service().get_booking_by_id(booking_id)
    if not booking or booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Booking not found")
    result = get_booking_service().check_in(booking_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot check in - booking is not in confirmed status")
    return result


@router.post("/{booking_id}/check-out", response_model=BookingResponse)
async def check_out(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Check out from parking. Moves booking from active → completed with final price."""
    booking = get_booking_service().get_booking_by_id(booking_id)
    if not booking or booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Booking not found")
    result = get_booking_service().check_out(booking_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot check out - booking is not in active status")
    return result


@router.post("/{booking_id}/extend", response_model=BookingResponse)
async def extend_booking(
    booking_id: str,
    data: BookingExtendRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extend an active booking by additional hours."""
    try:
        return get_booking_service().extend_booking(
            booking_id, current_user["user_id"], data.additional_hours
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
