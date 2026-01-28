"""Parking API Routes"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.models import ParkingResponse, ParkingSlot
from app.core.security import get_current_user
from app.services import get_parking_service

router = APIRouter(prefix="/parkings", tags=["Parkings"])


@router.get("", response_model=List[ParkingResponse])
async def get_all_parkings(current_user: dict = Depends(get_current_user)):
    return get_parking_service().get_all_parkings()


@router.get("/search", response_model=List[ParkingResponse])
async def search_nearby(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(10),
    sort_by: str = Query("distance"),
    current_user: dict = Depends(get_current_user)
):
    return get_parking_service().search_nearby(latitude, longitude, radius_km, sort_by)


@router.get("/{parking_id}", response_model=ParkingResponse)
async def get_parking(parking_id: str, current_user: dict = Depends(get_current_user)):
    parking = get_parking_service().get_parking_by_id(parking_id)
    if not parking:
        raise HTTPException(status_code=404, detail="Parking not found")
    return parking


@router.get("/{parking_id}/slots", response_model=List[ParkingSlot])
async def get_slots(parking_id: str, current_user: dict = Depends(get_current_user)):
    service = get_parking_service()
    if not service.get_parking_by_id(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return service.get_parking_slots(parking_id)


@router.get("/{parking_id}/slots/available", response_model=List[ParkingSlot])
async def get_available_slots(parking_id: str, current_user: dict = Depends(get_current_user)):
    service = get_parking_service()
    if not service.get_parking_by_id(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return service.get_parking_slots(parking_id, available_only=True)
