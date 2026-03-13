"""Admin API Routes"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.models import (
    DashboardStats, GateControlRequest, AlertResponse,
    VehicleLogResponse, AdminSendNotificationRequest, SupportTicketResponse,
    ParkingCreate, ParkingUpdate, ParkingResponse, UserStatusUpdate
)
from app.core.security import get_current_admin
from app.services import (
    get_parking_service, get_alert_service, get_vehicle_log_service,
    get_notification_service, get_support_service
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(current_user: dict = Depends(get_current_admin)):
    ps = get_parking_service()
    parkings = ps.get_all_parkings()

    total_slots = sum(p["total_slots"] for p in parkings)
    available = sum(p["available_slots"] for p in parkings)
    occupied = sum(p["occupied_slots"] for p in parkings)
    active = len([b for b in ps._demo_bookings.values() if b["status"] in ["confirmed", "active"]])
    active_alerts = len([a for a in ps._alerts.values() if a["status"] == "active"])

    total_revenue = sum(b["total_amount"] for b in ps._demo_bookings.values()
                        if b["payment_status"] == "completed")

    return DashboardStats(
        total_parkings=len(parkings),
        total_slots=total_slots,
        available_slots=available,
        occupied_slots=occupied,
        total_users=len(ps._demo_users),
        active_bookings=active,
        today_bookings=len(ps._demo_bookings),
        today_revenue=round(total_revenue, 2),
        pending_alerts=active_alerts,
        currency="EGP"
    )


@router.post("/gates/{parking_id}/control")
async def gate_control(parking_id: str, data: GateControlRequest, current_user: dict = Depends(get_current_admin)):
    if not get_parking_service().get_parking_by_id(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return {"success": True, "message": f"Gate {data.gate_type} {data.action} sent", "parking_id": parking_id}


# ─── Bookings ─────────────────────────────────────────

@router.get("/bookings")
async def all_bookings(
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin)
):
    bookings = list(get_parking_service()._demo_bookings.values())
    if status:
        bookings = [b for b in bookings if b["status"] == status]
    return sorted(bookings, key=lambda x: x["created_at"], reverse=True)


# ─── Users ────────────────────────────────────────────

@router.get("/users")
async def all_users(current_user: dict = Depends(get_current_admin)):
    return [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in get_parking_service()._demo_users.values()
    ]


@router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_admin)):
    user = get_parking_service()._demo_users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {k: v for k, v in user.items() if k != "password_hash"}


# ─── Alerts ───────────────────────────────────────────

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin)
):
    return get_alert_service().get_all_alerts(status)


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, current_user: dict = Depends(get_current_admin)):
    alert = get_alert_service().get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_admin)):
    alert = get_alert_service().acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: str, current_user: dict = Depends(get_current_admin)):
    alert = get_alert_service().resolve_alert(alert_id, current_user["user_id"])
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# ─── Vehicle Logs ────────────────────────────────────

@router.get("/vehicles/logs", response_model=List[VehicleLogResponse])
async def get_vehicle_logs(
    parking_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_admin)
):
    return get_vehicle_log_service().get_logs(parking_id, action, limit)


# ─── Notifications ───────────────────────────────────

@router.post("/notifications/send")
async def send_notification(data: AdminSendNotificationRequest, current_user: dict = Depends(get_current_admin)):
    ns = get_notification_service()

    if data.user_id:
        user = get_parking_service()._demo_users.get(data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        notif = ns.create_notification(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            notification_type=data.notification_type.value
        )
        return {"success": True, "message": "Notification sent", "notification_id": notif["id"]}
    else:
        count = ns.broadcast_notification(
            title=data.title,
            message=data.message,
            notification_type=data.notification_type.value
        )
        return {"success": True, "message": f"Notification broadcast to {count} users"}


# ─── Support Tickets ─────────────────────────────────

@router.get("/support/tickets", response_model=List[SupportTicketResponse])
async def get_all_tickets(current_user: dict = Depends(get_current_admin)):
    return get_support_service().get_all_tickets()


@router.put("/support/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: str = Query(..., description="new status: open, in_progress, resolved, closed"),
    current_user: dict = Depends(get_current_admin)
):
    ticket = get_support_service().update_ticket_status(ticket_id, status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# ─── Parking Management (CRUD) ──────────────────────

@router.get("/parkings")
async def admin_get_parkings(current_user: dict = Depends(get_current_admin)):
    """Get all parkings with full details for admin."""
    return get_parking_service().get_all_parkings()


@router.post("/parkings", response_model=ParkingResponse)
async def admin_create_parking(data: ParkingCreate, current_user: dict = Depends(get_current_admin)):
    """Create a new parking location."""
    parking = get_parking_service().create_parking(data.model_dump())
    return parking


@router.put("/parkings/{parking_id}", response_model=ParkingResponse)
async def admin_update_parking(parking_id: str, data: ParkingUpdate, current_user: dict = Depends(get_current_admin)):
    """Update parking details (rates, amenities, status, etc.)."""
    parking = get_parking_service().update_parking(parking_id, data.model_dump(exclude_none=True))
    if not parking:
        raise HTTPException(status_code=404, detail="Parking not found")
    return parking


@router.delete("/parkings/{parking_id}")
async def admin_delete_parking(parking_id: str, current_user: dict = Depends(get_current_admin)):
    """Deactivate a parking location (soft delete)."""
    if not get_parking_service().delete_parking(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return {"success": True, "message": f"Parking {parking_id} deactivated"}


@router.get("/parkings/{parking_id}/slots")
async def admin_get_slots(parking_id: str, current_user: dict = Depends(get_current_admin)):
    """Get all slots for a parking (admin view)."""
    ps = get_parking_service()
    if not ps.get_parking_by_id(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return ps.get_parking_slots(parking_id)


# ─── User Management ────────────────────────────────

@router.put("/users/{user_id}/suspend")
async def suspend_user(user_id: str, data: UserStatusUpdate, current_user: dict = Depends(get_current_admin)):
    """Suspend or activate a user account."""
    ps = get_parking_service()
    user = ps._demo_users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Cannot modify admin accounts")

    user["is_active"] = data.is_active
    status = "activated" if data.is_active else "suspended"

    if not data.is_active and data.reason:
        get_notification_service().create_notification(
            user_id=user_id,
            title="Account Suspended",
            message=f"Your account has been suspended. Reason: {data.reason}",
            notification_type="security"
        )

    return {"success": True, "user_id": user_id, "status": status, "is_active": data.is_active}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_admin)):
    """Delete a user account."""
    ps = get_parking_service()
    user = ps._demo_users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin accounts")

    del ps._demo_users[user_id]
    return {"success": True, "message": f"User {user_id} deleted"}
