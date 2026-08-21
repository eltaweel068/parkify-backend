# Parkify Backend

Backend API for Parkify — a smart parking management system that automates vehicle verification, slot assignment, booking management, and real-time IoT integration for parking facilities.

## Overview

Parkify eliminates manual ticketing by using AI-powered license plate recognition (ALPR) at entry/exit gates, real-time slot monitoring via IoT sensors, and fire/weapon detection through surveillance cameras. The backend serves both the mobile app used by drivers and the admin dashboard maintained by the frontend team.


---

## Tech Stack

- **Framework:** ASP.NET Core (.NET 10)
- **Language:** C#
- **Database:** PostgreSQL (hosted on Supabase)
- **Real-time:** WebSockets (built-in ASP.NET Core)
- **Authentication:** JWT (access + refresh tokens), device key auth for IoT
- **Deployment:** [Monsterasp](https://www.monsterasp.net/)

---

## System Architecture

```
Hardware Layer
  ESP32 gate controller    →  entry/exit gate
  Entry camera             →  license plate recognition (ALPR)
  Surveillance camera      →  fire and weapon detection

Processing Layer
  ALPR model (YOLO11n + EasyOCR)   →  reads license plates
  Fire model (YOLOv11x)            →  detects fire/smoke
  Weapon model (YOLOv8m)           →  detects weapons/theft

Backend Layer  (this repository)
  ASP.NET Core REST API
  PostgreSQL on Supabase
  WebSocket server for real-time events

Application Layer
  Mobile app (drivers)
  Admin dashboard (separate frontend app, built by frontend team)
```

---

## Project Structure

```
Controllers/       API route handlers (Auth, Users, Parkings, Bookings, Admin, IoT, ...)
DTOs/              Request/response data transfer objects
Models/            Database entity models
Data/              DbContext and database configuration
Services/          Business logic layer
Migrations/        EF Core database migrations
WebSockets/        WebSocket hub and real-time event handlers
Properties/        Launch settings
Program.cs         App startup, middleware, and route registration
schema.sql         Raw SQL schema for reference
appsettings.json   Configuration template (secrets are empty — use environment variables)
```

---

## Getting Started

### Prerequisites

- .NET 10 SDK
- PostgreSQL database (Supabase)

### Configuration

Copy `appsettings.json` and fill in your values. Never commit real secrets.

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=...;Database=postgres;Username=...;Password=...;SSL Mode=Require;Trust Server Certificate=true"
  },
  "Jwt": {
    "SecretKey": "your-secret-key-minimum-32-characters",
    "Issuer": "parkify-api",
    "Audience": "parkify-app",
    "AccessTokenExpiryMinutes": 60,
    "RefreshTokenExpiryDays": 7
  }
}
```

Set real values via environment variables on the server — do not put secrets in the file.

### Run Locally

```bash
dotnet restore
dotnet run
```

The API will be available at `https://localhost:6614`.

---

## API Overview

All requests and responses use JSON with `snake_case` keys.  
All protected endpoints require: `Authorization: Bearer <access_token>`

### Endpoint Groups

| Group | Base Path | Auth |
|-------|-----------|------|
| Auth | `/api/v1/auth` | None |
| Users | `/api/v1/users` | JWT |
| Parkings | `/api/v1/parkings` | JWT |
| Bookings | `/api/v1/bookings` | JWT |
| Favorites | `/api/v1/favorites` | JWT |
| Notifications | `/api/v1/notifications` | JWT |
| Support | `/api/v1/support` | JWT |
| Admin | `/api/v1/admin` | JWT (admin role) |
| IoT | `/api/v1/iot` | Device key |
| WebSockets | `/ws/...` | JWT or device key |



### Authentication Flow

```
POST /api/v1/auth/register   →  access_token + refresh_token
POST /api/v1/auth/login      →  access_token + refresh_token
POST /api/v1/auth/refresh    →  new access_token
```

### Booking Status Flow

```
confirmed  →  active (check-in)  →  completed (check-out)
confirmed  →  cancelled
```

Pricing: `amount = rate_per_hour x hours`, `fees = amount x 5%`, `total = amount + fees`

---

## WebSockets

Production uses WSS (WebSocket Secure). 

| Channel | Who connects | Events received |
|---------|-------------|-----------------|
| `/ws/parking/{parkingId}` | Mobile app | Live slot updates |
| `/ws/admin` | Admin dashboard (separate frontend) | All events: gate, slot, plate, fire, theft |
| `/ws/gate/{parkingId}?device_key=xxx` | ESP32 | Gate commands |

---

## IoT Integration (ESP32)

IoT endpoints do not use JWT. Authentication is via a `device_key` query parameter stored per parking in the database.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/iot/parking-status` | Get real-time slot counts |
| `POST /api/v1/iot/plate-detect` | Report ALPR plate detection (triggers auto check-in/out) |
| `POST /api/v1/iot/fire-alert` | Report fire detection event |
| `POST /api/v1/iot/theft-alert` | Report weapon/suspicious activity detection |
| `POST /api/v1/iot/slot-update` | Update a single slot status from sensor |
| `POST /api/v1/iot/gate-control` | Send gate open/close command |

### Automatic Side Effects

| ESP32 Event | Backend Action |
|-------------|---------------|
| Plate detected, entry, valid booking | Checks in booking, opens gate via WebSocket |
| Plate detected, exit, active booking | Checks out booking, opens gate, notifies spot watchers |
| Plate detected, exit, no booking | Opens gate, no booking action |
| Plate detected, entry, no booking | Creates security alert, does not open gate |
| Fire alert | Creates critical alert, broadcasts notification to all users |
| Theft alert | Creates high severity alert, broadcasts security notification to all users |
| Slot update to available | Notifies all users watching that parking |

### ESP32 Connection Example (HTTPS)

```cpp
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

const char* BASE_URL   = "";
const char* PARKING_ID = "your-parking-uuid";
const char* DEVICE_KEY = "your-device-key";

WiFiClientSecure client;
client.setInsecure();

HTTPClient http;
String url = String(BASE_URL) + "/api/v1/iot/plate-detect"
           + "?parking_id=" + PARKING_ID
           + "&plate=ABC123"
           + "&action=entry"
           + "&device_key=" + DEVICE_KEY;
http.begin(client, url);
int statusCode = http.POST("");
http.end();
```

### ESP32 WebSocket Connection (Gate Channel)

```cpp
#include <WebSocketsClient.h>

WebSocketsClient ws;

void setup() {
    ws.beginSSL(
        "url",
        443,
        "/ws/gate/YOUR_PARKING_UUID?device_key=YOUR_DEVICE_KEY"
    );
    ws.onEvent(onWsEvent);
    ws.setReconnectInterval(5000);
}

void onWsEvent(WStype_t type, uint8_t* payload, size_t length) {
    if (type == WStype_TEXT) {
        // {"type": "gate_command", "gate_type": "entry", "action": "open"}
    }
}
```

---

## Database Schema

PostgreSQL database with 13 tables.

| Table | Description |
|-------|-------------|
| `users` | All users (drivers and admins) |
| `cars` | Vehicles owned by users |
| `payment_methods` | Saved payment cards per user |
| `parkings` | Physical parking facilities |
| `parking_slots` | Individual slots per parking, auto-generated on creation |
| `bookings` | All reservations |
| `favorites` | User-saved parkings (many-to-many) |
| `notifications` | In-app notifications |
| `alerts` | Fire, theft, and security events from IoT |
| `vehicle_logs` | ALPR entry/exit records per gate |
| `support_tickets` | User help requests |
| `spot_watchers` | Users waiting for a slot to open (many-to-many) |
| `reset_codes` | OTP codes for password reset |

See `schema.sql` for the full SQL schema.

---

## Admin API

Admin endpoints are under `/api/v1/admin` and require a JWT from a user with `role: admin`.

Key capabilities:
- Dashboard statistics (total slots, revenue, active bookings, pending alerts)
- Full booking management (view, check-in, check-out, cancel any booking)
- User management (list, view, suspend, delete)
- Parking management (create, update, deactivate, view slots)
- Alert lifecycle (view fire/theft alerts, acknowledge, resolve)
- Vehicle logs (ALPR entry/exit history with confidence scores)
- Gate control (manually open/close entry or exit gate)
- Send notifications to individual users or broadcast to all
- Support ticket management (view all tickets, update status)
