# IoT Integration Edits (Models + API)

This file lists the required IoT-side edits so `smart_gate/src/gate.py` works correctly with the backend API.

## Backend API change added

Implemented endpoint:

- `GET /api/v1/iot/parking-status`

Query params:

- `parking_id`
- `device_key`

Returns:

- `total_slots`
- `occupied_slots`
- `available_slots`
- `is_full`

---

## Required edits in `smart_gate/src/gate.py`

### 1) Fix plate authorization check

Current behavior treats any HTTP 200 as authorized.  
Use the response `verified` field:

```python
def check_plate(plate: str, confidence: float) -> bool:
    resp = requests.post(..., timeout=5)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    return resp.status_code == 200 and data.get("verified", False) is True
```

### 2) Replace user endpoint with IoT endpoint for parking counters

Replace:

- `GET /api/v1/parkings/{parking_id}/slots/available` (needs JWT)

With:

- `GET /api/v1/iot/parking-status` (uses `device_key`)

Example:

```python
def get_parking_status() -> dict:
    resp = requests.get(
        f"{BACKEND_URL}/api/v1/iot/parking-status",
        params={"parking_id": PARKING_ID, "device_key": DEVICE_KEY},
        timeout=5,
    )
    if resp.status_code == 200:
        return resp.json()
    return {"success": False}
```

### 3) Remove hardcoded capacity dependency

Do not use a hardcoded `TOTAL_SPOTS` for logic/HUD.  
Use backend values from `parking-status`:

- `total_slots`
- `available_slots`
- `is_full`

### 4) Do not maintain occupancy only with local decrements

Avoid relying on:

- `cached_slots -= 1`

Use backend counters as the source of truth (refresh frequently, and/or send slot updates).

### 5) Persist occupancy for new visitor flow

When opening for a new visitor (`/open_new`), also send slot occupancy update to backend (or a booking flow) so backend state stays consistent.

If you have a known slot sensor event, call:

- `POST /api/v1/iot/slot-update`
  - `parking_id`
  - `slot_number`
  - `status=occupied`
  - `device_key`

### 6) Make model path portable

Replace absolute Windows path:

- `MODEL_PATH = "D:\\graduation_project\\best.pt"`

With a project-relative path, for example:

```python
from pathlib import Path
MODEL_PATH = str(Path(__file__).with_name("best.pt"))
```

---

## Optional ESP32 (`src/main.cpp`) improvements

1. Replace `delay(GATE_OPEN_MS)` with non-blocking timing (`millis`) to avoid blocking HTTP handling.
2. Add optional `/car_exit` endpoint if you want explicit exit counting from gate controller side.
