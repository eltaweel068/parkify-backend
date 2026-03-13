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
                # ALPR detected a plate - verify against bookings
                print(f"Plate detected: {msg}")
                from app.services import get_vehicle_log_service, get_booking_service, get_alert_service, get_notification_service, get_parking_service
                plate = msg.get("plate", "Unknown")
                action_type = msg.get("action", "entry")
                gate = msg.get("gate", "Gate A")

                get_vehicle_log_service().add_log(
                    parking_id=parking_id,
                    vehicle_plate=plate,
                    action=action_type,
                    gate=gate,
                    confidence=msg.get("confidence")
                )

                bs = get_booking_service()
                verified = False
                booking_id = None

                if action_type == "entry":
                    booking = bs.find_booking_by_plate(parking_id, plate, ["confirmed"])
                    if booking:
                        verified = True
                        booking_id = booking["id"]
                        bs.check_in(booking_id)
                        await websocket.send_json({
                            "type": "gate_command", "gate_type": "entry", "action": "open"
                        })
                    else:
                        get_alert_service().create_alert(
                            parking_id, "security", "medium",
                            f"Unregistered vehicle: {plate} at {gate}"
                        )
                elif action_type == "exit":
                    booking = bs.find_booking_by_plate(parking_id, plate, ["active"])
                    if booking:
                        verified = True
                        booking_id = booking["id"]
                        bs.check_out(booking_id)
                        # Notify spot watchers
                        ps = get_parking_service()
                        watchers = ps.get_spot_watchers(parking_id)
                        if watchers:
                            parking_data = ps.get_parking_by_id(parking_id)
                            ns = get_notification_service()
                            for watcher_id in watchers:
                                ns.create_notification(
                                    user_id=watcher_id,
                                    title="Spot Available!",
                                    message=f"A spot just opened at {parking_data['name']}. Book now!",
                                    notification_type="booking",
                                    data={"parking_id": parking_id}
                                )
                                ps.remove_spot_watcher(parking_id, watcher_id)
                    # Always open gate for exits
                    await websocket.send_json({
                        "type": "gate_command", "gate_type": "exit", "action": "open"
                    })

                await mgr.send_to_channel("admin", {
                    "type": "plate_detected",
                    "parking_id": parking_id,
                    "data": {**msg, "verified": verified, "booking_id": booking_id}
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
    Verifies plate against active bookings and auto-controls gate.

    Flow:
    - ENTRY: plate matched to confirmed booking → open gate + check-in
    - EXIT: plate matched to active booking → open gate + check-out
    - NO MATCH: gate stays closed, admin alerted about unregistered vehicle
    """
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    from app.services import get_vehicle_log_service, get_booking_service, get_alert_service, get_notification_service
    log = get_vehicle_log_service().add_log(parking_id, plate, action, gate, confidence)
    bs = get_booking_service()
    mgr = get_ws_manager()

    verified = False
    booking_id = None
    gate_command = "none"
    message = ""

    if action == "entry":
        # Look for a confirmed booking with this plate at this parking
        booking = bs.find_booking_by_plate(parking_id, plate, ["confirmed"])
        if booking:
            verified = True
            booking_id = booking["id"]
            gate_command = "open"
            message = f"Vehicle verified. Booking {booking_id} checked in."
            # Auto check-in
            bs.check_in(booking_id)
            # Send gate open command to ESP32
            await mgr.send_to_channel(f"gate:{parking_id}", {
                "type": "gate_command",
                "gate_type": "entry",
                "action": "open"
            })
        else:
            message = f"Unregistered vehicle {plate} at {gate}. No matching booking found."
            # Alert admin about unregistered vehicle
            get_alert_service().create_alert(
                parking_id, "security", "medium",
                f"Unregistered vehicle detected: {plate} at {gate} (confidence: {confidence})"
            )

    elif action == "exit":
        # Look for an active booking with this plate
        booking = bs.find_booking_by_plate(parking_id, plate, ["active"])
        if booking:
            verified = True
            booking_id = booking["id"]
            gate_command = "open"
            message = f"Vehicle verified. Booking {booking_id} checked out."
            # Auto check-out
            bs.check_out(booking_id)
            # Send gate open command
            await mgr.send_to_channel(f"gate:{parking_id}", {
                "type": "gate_command",
                "gate_type": "exit",
                "action": "open"
            })
            # Notify spot watchers
            from app.services import get_parking_service
            ps = get_parking_service()
            watchers = ps.get_spot_watchers(parking_id)
            if watchers:
                parking = ps.get_parking_by_id(parking_id)
                ns = get_notification_service()
                for watcher_id in watchers:
                    ns.create_notification(
                        user_id=watcher_id,
                        title="Spot Available!",
                        message=f"A parking spot just opened up at {parking['name']}. Book now!",
                        notification_type="booking",
                        data={"parking_id": parking_id}
                    )
                    ps.remove_spot_watcher(parking_id, watcher_id)
        else:
            # Let them exit anyway, but alert admin
            gate_command = "open"
            message = f"Vehicle {plate} exiting without active booking. Gate opened."
            await mgr.send_to_channel(f"gate:{parking_id}", {
                "type": "gate_command",
                "gate_type": "exit",
                "action": "open"
            })

    # Broadcast to admin
    await mgr.send_to_channel("admin", {
        "type": "plate_detected",
        "parking_id": parking_id,
        "data": {
            "plate": plate, "action": action, "gate": gate,
            "confidence": confidence, "verified": verified,
            "booking_id": booking_id, "gate_command": gate_command
        }
    })

    return {
        "success": True,
        "verified": verified,
        "log_id": log["id"],
        "plate": plate,
        "action": action,
        "gate_command": gate_command,
        "booking_id": booking_id,
        "message": message
    }


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


@app.post("/api/v1/iot/theft-alert", tags=["IoT / Hardware"])
async def iot_theft_alert(
    parking_id: str = Query(...),
    message: str = Query("Suspicious activity detected"),
    confidence: float = Query(0.80),
    weapon_type: str = Query("unknown", description="Detected weapon type: gun, knife, unknown"),
    device_key: str = Query(...)
):
    """HTTP endpoint for theft/weapon detection system to report security alerts."""
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key",
            "parking_3": "esp32_parking3_key", "parking_4": "esp32_parking4_key",
            "parking_5": "esp32_parking5_key"}
    if device_key != KEYS.get(parking_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid device key")

    from app.services import get_alert_service, get_notification_service
    alert = get_alert_service().create_alert(parking_id, "theft", "high",
                                              f"{message} - weapon: {weapon_type} (confidence: {confidence})")

    get_notification_service().broadcast_notification(
        title="Security Alert!",
        message=f"Suspicious activity detected at {alert['parking_name']}. Security has been notified.",
        notification_type="security"
    )

    mgr = get_ws_manager()
    await mgr.send_to_channel("admin", {
        "type": "theft_alert",
        "parking_id": parking_id,
        "data": {"message": message, "confidence": confidence, "weapon_type": weapon_type, "alert_id": alert["id"]}
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

    # Notify spot watchers when a slot becomes available
    if status == "available" and old_status != "available":
        from app.services import get_notification_service
        watchers = ps.get_spot_watchers(parking_id)
        if watchers and parking:
            ns = get_notification_service()
            for watcher_id in watchers:
                ns.create_notification(
                    user_id=watcher_id,
                    title="Spot Available!",
                    message=f"A spot just opened at {parking['name']}. Book now!",
                    notification_type="booking",
                    data={"parking_id": parking_id}
                )
                ps.remove_spot_watcher(parking_id, watcher_id)

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
