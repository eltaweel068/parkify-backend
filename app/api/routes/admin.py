"""Admin API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from app.models import DashboardStats, GateControlRequest
from app.core.security import get_current_admin
from app.services import get_parking_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(current_user: dict = Depends(get_current_admin)):
    ps = get_parking_service()
    parkings = ps.get_all_parkings()
    
    total_slots = sum(p["total_slots"] for p in parkings)
    available = sum(p["available_slots"] for p in parkings)
    occupied = sum(p["occupied_slots"] for p in parkings)
    active = len([b for b in ps._demo_bookings.values() if b["status"] in ["confirmed", "active"]])
    
    return DashboardStats(
        total_parkings=len(parkings),
        total_slots=total_slots,
        available_slots=available,
        occupied_slots=occupied,
        total_users=len(ps._demo_users),
        active_bookings=active,
        today_bookings=5,
        today_revenue=1250.0,
        pending_alerts=2,
        currency="EGP"
    )


@router.post("/gates/{parking_id}/control")
async def gate_control(parking_id: str, data: GateControlRequest, current_user: dict = Depends(get_current_admin)):
    if not get_parking_service().get_parking_by_id(parking_id):
        raise HTTPException(status_code=404, detail="Parking not found")
    return {"success": True, "message": f"Gate {data.gate_type} {data.action} sent", "parking_id": parking_id}


@router.get("/bookings")
async def all_bookings(current_user: dict = Depends(get_current_admin)):
    return list(get_parking_service()._demo_bookings.values())


@router.get("/users")
async def all_users(current_user: dict = Depends(get_current_admin)):
    return [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in get_parking_service()._demo_users.values()
    ]
