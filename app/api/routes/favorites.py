"""Favorites API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import FavoriteResponse
from app.core.security import get_current_user
from app.services import get_favorite_service

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=List[FavoriteResponse])
async def get_favorites(current_user: dict = Depends(get_current_user)):
    return get_favorite_service().get_user_favorites(current_user["user_id"])


@router.post("/{parking_id}", response_model=FavoriteResponse)
async def add_favorite(parking_id: str, current_user: dict = Depends(get_current_user)):
    fav = get_favorite_service().add_favorite(current_user["user_id"], parking_id)
    if not fav:
        raise HTTPException(status_code=404, detail="Parking not found")
    return fav


@router.delete("/{parking_id}")
async def remove_favorite(parking_id: str, current_user: dict = Depends(get_current_user)):
    if not get_favorite_service().remove_favorite(current_user["user_id"], parking_id):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"success": True, "message": "Removed from favorites"}


@router.get("/{parking_id}/check")
async def check_favorite(parking_id: str, current_user: dict = Depends(get_current_user)):
    is_fav = get_favorite_service().is_favorited(current_user["user_id"], parking_id)
    return {"is_favorited": is_fav}
