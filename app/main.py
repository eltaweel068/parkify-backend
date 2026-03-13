"""
Parkify - Smart Parking Management System
Local Development Server - FIXED VERSION
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os

from app.api.routes import auth, parking, bookings, admin, users, notifications, favorites, support
from app.websockets import get_ws_manager

app = FastAPI(
    title="Parkify API",
    description="""
    Smart Parking Management System API

    ## Demo Accounts
    - **Admin:** admin@parkify.com / admin123
    - **User:** user@parkify.com / user123

    ## Features
    - JWT Authentication (email/password + social login)
    - Password Reset (email & phone OTP)
    - User Profile & Car Management
    - Parking Search, Filter & Favorites
    - Booking System with QR Codes
    - Payment Methods Management
    - Notifications System
    - Support Tickets
    - Real-time WebSocket Updates
    - Admin Dashboard (API + Web UI)
    - Admin Alerts (Fire/Theft Detection)
    - Vehicle Entry/Exit Logs (ALPR)
    - ESP32 Gate Control via WebSocket
    """,
    version="3.0.0"
)

# CORS - Allow all for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(parking.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(support.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Parkify API",
        "version": "3.0.0",
        "docs": "/docs",
        "admin_dashboard": "/dashboard",
        "demo_accounts": {
            "admin": "admin@parkify.com / admin123",
            "user": "user@parkify.com / user123"
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "service": "parkify-api", "version": "3.0.0"}


# ─── Admin Dashboard (Web UI) ──────────────────────

@app.get("/dashboard", response_class=HTMLResponse, tags=["Admin Dashboard"])
async def admin_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard.html")
    with open(dashboard_path, "r") as f:
        return HTMLResponse(content=f.read())


# ─── WebSocket Endpoints ──────────────────────────

@app.websocket("/ws/parking/{parking_id}")
async def ws_parking(websocket: WebSocket, parking_id: str):
    mgr = get_ws_manager()
    channel = f"parking:{parking_id}"
    await mgr.connect(websocket, channel)
    try:
        await websocket.send_json({"type": "connected", "parking_id": parking_id})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await mgr.disconnect(websocket, channel)


@app.websocket("/ws/admin")
async def ws_admin(websocket: WebSocket):
    mgr = get_ws_manager()
    await mgr.connect(websocket, "admin")
    try:
        await websocket.send_json({"type": "connected", "channel": "admin"})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await mgr.disconnect(websocket, "admin")


@app.websocket("/ws/gate/{parking_id}")
async def ws_gate(websocket: WebSocket, parking_id: str, device_key: str = Query(None)):
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        await websocket.close(code=4001)
        return

    mgr = get_ws_manager()
    channel = f"gate:{parking_id}"
    await mgr.connect(websocket, channel)
    print(f"ESP32 connected: {parking_id}")

    try:
        await websocket.send_json({"type": "connected", "parking_id": parking_id})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg.get("type") == "gate_status":
                print(f"Gate status: {msg}")
                # Broadcast to admin channel
                await mgr.send_to_channel("admin", {
                    "type": "gate_update",
                    "parking_id": parking_id,
                    "data": msg
                })
            elif msg.get("type") == "slot_update":
                # ESP32 reports slot sensor change
                print(f"Slot update: {msg}")
                await mgr.send_to_channel(f"parking:{parking_id}", {
                    "type": "slot_update",
                    "parking_id": parking_id,
                    "data": msg
                })
                await mgr.send_to_channel("admin", {
                    "type": "slot_update",
                    "parking_id": parking_id,
                    "data": msg
                })
            elif msg.get("type") == "plate_detected":
                # ALPR detected a plate
                print(f"Plate detected: {msg}")
                from app.services import get_vehicle_log_service
                get_vehicle_log_service().add_log(
                    parking_id=parking_id,
                    vehicle_plate=msg.get("plate", "Unknown"),
                    action=msg.get("action", "entry"),
                    gate=msg.get("gate", "Gate A"),
                    confidence=msg.get("confidence")
                )
                await mgr.send_to_channel("admin", {
                    "type": "plate_detected",
                    "parking_id": parking_id,
                    "data": msg
                })
            elif msg.get("type") == "fire_alert":
                # Fire detection model triggered
                print(f"FIRE ALERT: {msg}")
                from app.services import get_alert_service
                get_alert_service().create_alert(
                    parking_id=parking_id,
                    alert_type="fire",
                    severity="critical",
                    message=msg.get("message", "Fire detected by AI model")
                )
                await mgr.send_to_channel("admin", {
                    "type": "fire_alert",
                    "parking_id": parking_id,
                    "data": msg
                })
            elif msg.get("type") == "theft_alert":
                # Theft detection model triggered
                print(f"THEFT ALERT: {msg}")
                from app.services import get_alert_service
                get_alert_service().create_alert(
                    parking_id=parking_id,
                    alert_type="theft",
                    severity="high",
                    message=msg.get("message", "Suspicious activity detected by AI model")
                )
                await mgr.send_to_channel("admin", {
                    "type": "theft_alert",
                    "parking_id": parking_id,
                    "data": msg
                })
    except WebSocketDisconnect:
        print(f"ESP32 disconnected: {parking_id}")
        await mgr.disconnect(websocket, channel)


# ─── IoT / Hardware Endpoints ────────────────────────

@app.post("/api/v1/iot/plate-detect", tags=["IoT / Hardware"])
async def iot_plate_detect(
    parking_id: str = Query(...),
    plate: str = Query(...),
    action: str = Query("entry"),
    gate: str = Query("Gate A"),
    confidence: float = Query(0.95),
    device_key: str = Query(...)
):
    """
    HTTP endpoint for ESP32/ALPR to report detected license plates.
    Use this if WebSocket is not available.
    """
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    from app.services import get_vehicle_log_service
    log = get_vehicle_log_service().add_log(parking_id, plate, action, gate, confidence)

    mgr = get_ws_manager()
    await mgr.send_to_channel("admin", {
        "type": "plate_detected",
        "parking_id": parking_id,
        "data": {"plate": plate, "action": action, "gate": gate, "confidence": confidence}
    })

    return {"success": True, "log_id": log["id"], "plate": plate, "action": action}


@app.post("/api/v1/iot/fire-alert", tags=["IoT / Hardware"])
async def iot_fire_alert(
    parking_id: str = Query(...),
    message: str = Query("Fire detected"),
    confidence: float = Query(0.87),
    device_key: str = Query(...)
):
    """HTTP endpoint for fire detection system to report fire alerts."""
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    from app.services import get_alert_service, get_notification_service
    alert = get_alert_service().create_alert(parking_id, "fire", "critical",
                                              f"{message} (confidence: {confidence})")

    get_notification_service().broadcast_notification(
        title="Fire Alert!",
        message=f"Fire detected at {alert['parking_name']}. Please evacuate immediately.",
        notification_type="alert"
    )

    mgr = get_ws_manager()
    await mgr.send_to_channel("admin", {
        "type": "fire_alert",
        "parking_id": parking_id,
        "data": {"message": message, "confidence": confidence, "alert_id": alert["id"]}
    })

    return {"success": True, "alert_id": alert["id"]}


@app.post("/api/v1/iot/slot-update", tags=["IoT / Hardware"])
async def iot_slot_update(
    parking_id: str = Query(...),
    slot_number: str = Query(...),
    status: str = Query(..., description="available or occupied"),
    device_key: str = Query(...)
):
    """HTTP endpoint for ESP32 slot sensors to report occupancy changes."""
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    from app.services import get_parking_service
    ps = get_parking_service()
    slot_id = f"{parking_id}_slot_{slot_number}"
    slot = ps.get_slot_by_id(slot_id)
    if not slot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Slot not found")

    old_status = slot["status"]
    slot["status"] = status

    parking = ps.get_parking_by_id(parking_id)
    if parking and old_status != status:
        if status == "available" and old_status == "occupied":
            parking["available_slots"] += 1
            parking["occupied_slots"] -= 1
        elif status == "occupied" and old_status == "available":
            parking["available_slots"] -= 1
            parking["occupied_slots"] += 1

    mgr = get_ws_manager()
    await mgr.send_to_channel(f"parking:{parking_id}", {
        "type": "slot_update",
        "slot_id": slot_id,
        "slot_number": slot_number,
        "status": status
    })
    await mgr.send_to_channel("admin", {
        "type": "slot_update",
        "parking_id": parking_id,
        "slot_id": slot_id,
        "slot_number": slot_number,
        "status": status
    })

    return {"success": True, "slot_id": slot_id, "status": status}


@app.post("/api/v1/iot/gate-control", tags=["IoT / Hardware"])
async def iot_gate_response(
    parking_id: str = Query(...),
    gate_type: str = Query("entry"),
    action: str = Query("open"),
    device_key: str = Query(...)
):
    """Send gate open/close command to ESP32 via WebSocket."""
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    mgr = get_ws_manager()
    await mgr.send_to_channel(f"gate:{parking_id}", {
        "type": "gate_command",
        "gate_type": gate_type,
        "action": action
    })

    return {"success": True, "message": f"Gate {gate_type} {action} command sent to {parking_id}"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("  PARKIFY API - Local Development Server")
    print("="*50)
    print(f"\n  API:       http://localhost:8000")
    print(f"  Docs:      http://localhost:8000/docs")
    print(f"  Dashboard: http://localhost:8000/dashboard")
    print(f"\n  Demo Accounts:")
    print(f"    Admin: admin@parkify.com / admin123")
    print(f"    User:  amira@gmail.com   / user123")
    print("\n" + "="*50 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
