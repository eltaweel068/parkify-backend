"""
Parkify - Smart Parking Management System
Local Development Server - FIXED VERSION
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import json

from app.api.routes import auth, parking, bookings, admin
from app.websockets import get_ws_manager

app = FastAPI(
    title="Parkify API",
    description="""
    🅿️ Smart Parking Management System API
    
    ## Demo Accounts
    - **Admin:** admin@parkify.com / admin123
    - **User:** user@parkify.com / user123
    
    ## Features
    - 🔐 JWT Authentication
    - 🅿️ Parking Search & Management
    - 📅 Booking System
    - 📡 Real-time WebSocket Updates
    - 👨‍💼 Admin Dashboard API
    """,
    version="2.0.0"
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
app.include_router(parking.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🅿️ Welcome to Parkify API",
        "version": "2.0.0",
        "docs": "/docs",
        "demo_accounts": {
            "admin": "admin@parkify.com / admin123",
            "user": "user@parkify.com / user123"
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "service": "parkify-api"}


# WebSocket endpoints
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
    KEYS = {"parking_1": "esp32_parking1_key", "parking_2": "esp32_parking2_key", "parking_3": "esp32_parking3_key"}
    if device_key != KEYS.get(parking_id):
        await websocket.close(code=4001)
        return
    
    mgr = get_ws_manager()
    channel = f"gate:{parking_id}"
    await mgr.connect(websocket, channel)
    print(f"✅ ESP32 connected: {parking_id}")
    
    try:
        await websocket.send_json({"type": "connected", "parking_id": parking_id})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg.get("type") == "gate_status":
                print(f"📡 Gate: {msg}")
    except WebSocketDisconnect:
        print(f"❌ ESP32 disconnected: {parking_id}")
        await mgr.disconnect(websocket, channel)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🅿️  PARKIFY API - Local Development Server")
    print("="*50)
    print(f"\n📍 API:  http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    print(f"\n👤 Demo Accounts:")
    print(f"   Admin: admin@parkify.com / admin123")
    print(f"   User:  user@parkify.com / user123")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
