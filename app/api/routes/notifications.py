"""Notifications API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import NotificationResponse, UnreadCountResponse
from app.core.security import get_current_user
from app.services import get_notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(current_user: dict = Depends(get_current_user)):
    return get_notification_service().get_user_notifications(current_user["user_id"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(current_user: dict = Depends(get_current_user)):
    count = get_notification_service().get_unread_count(current_user["user_id"])
    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    notif = get_notification_service().mark_as_read(notification_id, current_user["user_id"])
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.put("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    count = get_notification_service().mark_all_read(current_user["user_id"])
    return {"success": True, "message": f"{count} notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    if not get_notification_service().delete_notification(notification_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "message": "Notification deleted"}
