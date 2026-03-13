"""Parking API Routes"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.models import ParkingResponse, ParkingSlot, ParkingFilterRequest
from app.core.security import get_current_user
from app.services import get_parking_service, get_favorite_service

router = APIRouter(prefix="/parkings", tags=["Parkings"])


@router.get("", response_model=List[ParkingResponse])
async def get_all_parkings(current_user: dict = Depends(get_current_user)):
    parkings = get_parking_service().get_all_parkings()
    fav_service = get_favorite_service()
    for p in parkings:
        p["is_favorited"] = fav_service.is_favorited(current_user["user_id"], p["id"])
    return parkings


@router.get("/search", response_model=List[ParkingResponse])
async def search_nearby(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(10),
    sort_by: str = Query("distance"),
    current_user: dict = Depends(get_current_user)
):
    parkings = get_parking_service().search_nearby(latitude, longitude, radius_km, sort_by)
    fav_service = get_favorite_service()
    for p in parkings:
        p["is_favorited"] = fav_service.is_favorited(current_user["user_id"], p["id"])
    return parkings


@router.get("/search-by-name", response_model=List[ParkingResponse])
async def search_by_name(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: dict = Depends(get_current_user)
):
    """Search parkings by name, description, address, or city."""
    parkings = get_parking_service().search_by_name(q)
    fav_service = get_favorite_service()
    for p in parkings:
        p["is_favorited"] = fav_service.is_favorited(current_user["user_id"], p["id"])
    return parkings


@router.post("/filter", response_model=List[ParkingResponse])
async def filter_parkings(
    filters: ParkingFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """Filter parkings by price, distance, type, amenities, and sort order."""
    parkings = get_parking_service().filter_parkings(
        lat=filters.latitude,
        lon=filters.longitude,
        radius_km=filters.radius_km,
        min_price=filters.min_price,
        max_price=filters.max_price,
        parking_type=filters.parking_type,
        sort_by=filters.sort_by,
        amenities=filters.amenities,
        available_only=filters.available_only
    )
    fav_service = get_favorite_service()
    for p in parkings:
        p["is_favorited"] = fav_service.is_favorited(current_user["user_id"], p["id"])
    return parkings


@router.get("/filter", response_model=List[ParkingResponse])
async def filter_parkings_get(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(10),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    parking_type: Optional[str] = Query(None),
    sort_by: str = Query("distance"),
    available_only: bool = Query(True),
    current_user: dict = Depends(get_current_user)
):
    """Filter parkings via GET query params."""
    parkings = get_parking_service().filter_parkings(
        lat=latitude,
        lon=longitude,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
        parking_type=parking_type,
        sort_by=sort_by,
        available_only=available_only
    )
    fav_service = get_favorite_service()
    for p in parkings:
        p["is_favorited"] = fav_service.is_favorited(current_user["user_id"], p["id"])
    return parkings


@router.get("/{parking_id}", response_model=ParkingResponse)
async def get_parking(parking_id: str, current_user: dict = Depends(get_current_user)):
    parking = get_parking_service().get_parking_by_id(parking_id)
    if not parking:
        raise HTTPException(status_code=404, detail="Parking not found")
    parking["is_favorited"] = get_favorite_service().is_favorited(current_user["user_id"], parking_id)
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
