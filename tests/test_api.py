"""
Parkify API Unit Tests
Tests all endpoints: auth, users, parkings, bookings, IoT, admin, etc.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


# ─── Fixtures ────────────────────────────────────────

@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
async def client(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def user_token(client):
    """Login as demo user and return token."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "amira@gmail.com",
        "password": "user123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
async def admin_token(client):
    """Login as admin and return token."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "admin@parkify.com",
        "password": "admin123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─── Root & Health ───────────────────────────────────

class TestRootHealth:
    @pytest.mark.anyio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Welcome to Parkify API"
        assert "version" in data

    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ─── Authentication ──────────────────────────────────

class TestAuth:
    @pytest.mark.anyio
    async def test_login_success(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "amira@gmail.com",
            "password": "user123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "amira@gmail.com"

    @pytest.mark.anyio
    async def test_login_wrong_password(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "amira@gmail.com",
            "password": "wrongpass"
        })
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "test123"
        })
        assert resp.status_code == 401  # Returns 401 for both wrong password and nonexistent user

    @pytest.mark.anyio
    async def test_register(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "name": "New User",
            "password": "test123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@test.com"

    @pytest.mark.anyio
    async def test_register_duplicate_email(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "amira@gmail.com",
            "name": "Duplicate",
            "password": "test123"
        })
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_refresh_token(self, client):
        login = await client.post("/api/v1/auth/login", json={
            "email": "amira@gmail.com",
            "password": "user123"
        })
        refresh = login.json()["refresh_token"]
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.anyio
    async def test_social_login(self, client):
        resp = await client.post("/api/v1/auth/social", json={
            "provider": "google",
            "token": "fake_token",
            "name": "Google User",
            "email": "google@test.com"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.anyio
    async def test_forgot_password_email(self, client):
        resp = await client.post("/api/v1/auth/forgot-password/email", json={
            "email": "amira@gmail.com"
        })
        assert resp.status_code == 200
        assert "demo_code" in resp.json()

    @pytest.mark.anyio
    async def test_forgot_password_phone(self, client):
        resp = await client.post("/api/v1/auth/forgot-password/phone", json={
            "phone": "+20 0967 834 888"
        })
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_verify_and_reset_password(self, client):
        # Get reset code
        forgot = await client.post("/api/v1/auth/forgot-password/email", json={
            "email": "ahmed@gmail.com"
        })
        code = forgot.json()["demo_code"]

        # Verify code
        verify = await client.post("/api/v1/auth/verify-code", json={
            "email": "ahmed@gmail.com",
            "code": code
        })
        assert verify.status_code == 200

        # Reset password
        reset = await client.post("/api/v1/auth/reset-password", json={
            "email": "ahmed@gmail.com",
            "code": code,
            "new_password": "newpass123"
        })
        assert reset.status_code == 200

        # Login with new password
        login = await client.post("/api/v1/auth/login", json={
            "email": "ahmed@gmail.com",
            "password": "newpass123"
        })
        assert login.status_code == 200

    @pytest.mark.anyio
    async def test_admin_login(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@parkify.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "admin"


# ─── User Profile ────────────────────────────────────

class TestUserProfile:
    @pytest.mark.anyio
    async def test_get_profile(self, client, user_token):
        resp = await client.get("/api/v1/users/profile", headers=auth(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "amira@gmail.com"
        assert "password_hash" not in data

    @pytest.mark.anyio
    async def test_update_profile(self, client, user_token):
        resp = await client.put("/api/v1/users/profile", headers=auth(user_token), json={
            "address": "Updated Address, Cairo"
        })
        assert resp.status_code == 200
        assert resp.json()["address"] == "Updated Address, Cairo"

    @pytest.mark.anyio
    async def test_unauthorized_access(self, client):
        resp = await client.get("/api/v1/users/profile")
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_invalid_token(self, client):
        resp = await client.get("/api/v1/users/profile",
                                headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


# ─── Cars ────────────────────────────────────────────

class TestCars:
    @pytest.mark.anyio
    async def test_list_cars(self, client, user_token):
        resp = await client.get("/api/v1/users/cars", headers=auth(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    @pytest.mark.anyio
    async def test_add_car(self, client, user_token):
        resp = await client.post("/api/v1/users/cars", headers=auth(user_token), json={
            "license_plate": "ت ث خ 9999",
            "make": "Toyota",
            "model": "Camry",
            "color": "Blue"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["license_plate"] == "ت ث خ 9999"
        assert "id" in data

    @pytest.mark.anyio
    async def test_update_car(self, client, user_token):
        # Get existing car
        cars = await client.get("/api/v1/users/cars", headers=auth(user_token))
        car_id = cars.json()[0]["id"]
        resp = await client.put(f"/api/v1/users/cars/{car_id}", headers=auth(user_token), json={
            "color": "Red"
        })
        assert resp.status_code == 200
        assert resp.json()["color"] == "Red"

    @pytest.mark.anyio
    async def test_set_default_car(self, client, user_token):
        cars = await client.get("/api/v1/users/cars", headers=auth(user_token))
        car_id = cars.json()[-1]["id"]
        resp = await client.put(f"/api/v1/users/cars/{car_id}/default", headers=auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["is_default"] is True


# ─── Payment Methods ─────────────────────────────────

class TestPaymentMethods:
    @pytest.mark.anyio
    async def test_list_methods(self, client, user_token):
        resp = await client.get("/api/v1/users/payment-methods", headers=auth(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.anyio
    async def test_add_method(self, client, user_token):
        resp = await client.post("/api/v1/users/payment-methods", headers=auth(user_token), json={
            "method_type": "card",
            "card_number": "4111111111119999",
            "card_holder": "Test User",
            "expiry_month": 12,
            "expiry_year": 2028
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["last_four"] == "9999"
        assert data["method_type"] == "card"


# ─── Parkings ────────────────────────────────────────

class TestParkings:
    @pytest.mark.anyio
    async def test_list_parkings(self, client, user_token):
        resp = await client.get("/api/v1/parkings", headers=auth(user_token))
        assert resp.status_code == 200
        parkings = resp.json()
        assert len(parkings) >= 7
        assert "is_favorited" in parkings[0]

    @pytest.mark.anyio
    async def test_search_nearby(self, client, user_token):
        resp = await client.get("/api/v1/parkings/search", headers=auth(user_token), params={
            "latitude": 30.0285,
            "longitude": 31.4085,
            "radius_km": 50
        })
        assert resp.status_code == 200
        parkings = resp.json()
        assert len(parkings) >= 1
        assert "distance_meters" in parkings[0]
        assert "walking_time_minutes" in parkings[0]

    @pytest.mark.anyio
    async def test_search_by_name(self, client, user_token):
        resp = await client.get("/api/v1/parkings/search-by-name", headers=auth(user_token), params={
            "q": "Cairo"
        })
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.anyio
    async def test_filter_parkings(self, client, user_token):
        resp = await client.post("/api/v1/parkings/filter", headers=auth(user_token), json={
            "max_price": 20.0,
            "parking_type": "covered",
            "available_only": True
        })
        assert resp.status_code == 200
        for p in resp.json():
            assert p["rate_per_hour"] <= 20.0
            assert p["parking_type"] == "covered"

    @pytest.mark.anyio
    async def test_get_parking(self, client, user_token):
        resp = await client.get("/api/v1/parkings/parking_1", headers=auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == "parking_1"

    @pytest.mark.anyio
    async def test_get_parking_not_found(self, client, user_token):
        resp = await client.get("/api/v1/parkings/nonexistent", headers=auth(user_token))
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_get_slots(self, client, user_token):
        resp = await client.get("/api/v1/parkings/parking_1/slots", headers=auth(user_token))
        assert resp.status_code == 200
        slots = resp.json()
        assert len(slots) >= 1
        assert "id" in slots[0]
        assert "status" in slots[0]

    @pytest.mark.anyio
    async def test_get_available_slots(self, client, user_token):
        resp = await client.get("/api/v1/parkings/parking_1/slots/available", headers=auth(user_token))
        assert resp.status_code == 200
        for s in resp.json():
            assert s["status"] == "available"


# ─── Spot Watcher (Subscription) ─────────────────────

class TestSpotWatcher:
    @pytest.mark.anyio
    async def test_watch_unwatch_flow(self, client, user_token):
        # Subscribe
        resp = await client.post("/api/v1/parkings/parking_1/watch", headers=auth(user_token))
        assert resp.status_code == 200

        # Check status
        resp = await client.get("/api/v1/parkings/parking_1/watch", headers=auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["is_watching"] is True

        # Unsubscribe
        resp = await client.delete("/api/v1/parkings/parking_1/watch", headers=auth(user_token))
        assert resp.status_code == 200

        # Verify
        resp = await client.get("/api/v1/parkings/parking_1/watch", headers=auth(user_token))
        assert resp.json()["is_watching"] is False


# ─── Bookings ────────────────────────────────────────

class TestBookings:
    @pytest.mark.anyio
    async def test_create_booking(self, client, user_token):
        resp = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_1",
            "slot_id": "parking_1_slot_A05",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T12:00:00",
            "payment_method": "card"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["parking_id"] == "parking_1"
        assert data["total_hours"] == 2.0
        assert data["amount"] == 40.0  # 2h * 20 EGP
        assert data["fees"] == 2.0     # 5% of 40
        assert data["total_amount"] == 42.0

    @pytest.mark.anyio
    async def test_create_booking_slot_taken(self, client, user_token):
        # Book a slot
        await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_2",
            "slot_id": "parking_2_slot_A05",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T12:00:00"
        })
        # Try same slot again
        resp = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_2",
            "slot_id": "parking_2_slot_A05",
            "vehicle_plate": "م ن و 5678",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T12:00:00"
        })
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_get_bookings(self, client, user_token):
        resp = await client.get("/api/v1/bookings", headers=auth(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.anyio
    async def test_get_active_booking(self, client, user_token):
        resp = await client.get("/api/v1/bookings/active", headers=auth(user_token))
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_get_booking_history(self, client, user_token):
        resp = await client.get("/api/v1/bookings/history", headers=auth(user_token))
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_booking_qr(self, client, user_token):
        # Create booking first
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_3",
            "slot_id": "parking_3_slot_A05",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-15T10:00:00",
            "end_time": "2026-03-15T12:00:00"
        })
        booking_id = create.json()["id"]
        resp = await client.get(f"/api/v1/bookings/{booking_id}/qr", headers=auth(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "qr_data" in data
        assert data["booking_id"] == booking_id

    @pytest.mark.anyio
    async def test_cancel_booking(self, client, user_token):
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_3",
            "slot_id": "parking_3_slot_B01",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-16T10:00:00",
            "end_time": "2026-03-16T12:00:00"
        })
        booking_id = create.json()["id"]
        resp = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        assert resp.json()["payment_status"] == "refunded"

    @pytest.mark.anyio
    async def test_extend_booking(self, client, user_token):
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_3",
            "slot_id": "parking_3_slot_B02",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-17T10:00:00",
            "end_time": "2026-03-17T12:00:00"
        })
        booking_id = create.json()["id"]
        # Check in first to make it active
        await client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=auth(user_token))
        resp = await client.post(f"/api/v1/bookings/{booking_id}/extend", headers=auth(user_token), json={
            "additional_hours": 1.0
        })
        assert resp.status_code == 200
        assert resp.json()["total_hours"] == 3.0


# ─── Check-in / Check-out ────────────────────────────

class TestCheckInOut:
    @pytest.mark.anyio
    async def test_checkin_checkout_flow(self, client, user_token):
        # Create booking
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_4",
            "slot_id": "parking_4_slot_A05",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-14T08:00:00",
            "end_time": "2026-03-14T10:00:00"
        })
        booking_id = create.json()["id"]
        assert create.json()["status"] == "confirmed"

        # Check in
        checkin = await client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=auth(user_token))
        assert checkin.status_code == 200
        assert checkin.json()["status"] == "active"

        # Check out
        checkout = await client.post(f"/api/v1/bookings/{booking_id}/check-out", headers=auth(user_token))
        assert checkout.status_code == 200
        assert checkout.json()["status"] == "completed"
        assert checkout.json()["actual_exit_time"] is not None

    @pytest.mark.anyio
    async def test_checkin_wrong_status(self, client, user_token):
        # Create and cancel booking
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_4",
            "slot_id": "parking_4_slot_B01",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T12:00:00"
        })
        booking_id = create.json()["id"]
        await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth(user_token))

        # Try to check in cancelled booking
        resp = await client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=auth(user_token))
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_checkout_without_checkin(self, client, user_token):
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_4",
            "slot_id": "parking_4_slot_B02",
            "vehicle_plate": "أ ب ج 1234",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T12:00:00"
        })
        booking_id = create.json()["id"]
        # Try check-out without check-in (status is confirmed, not active)
        resp = await client.post(f"/api/v1/bookings/{booking_id}/check-out", headers=auth(user_token))
        assert resp.status_code == 400


# ─── Favorites ───────────────────────────────────────

class TestFavorites:
    @pytest.mark.anyio
    async def test_favorites_flow(self, client, user_token):
        # Add favorite
        resp = await client.post("/api/v1/favorites/parking_3", headers=auth(user_token))
        assert resp.status_code == 200

        # Check favorited
        resp = await client.get("/api/v1/favorites/parking_3/check", headers=auth(user_token))
        assert resp.json()["is_favorited"] is True

        # List favorites
        resp = await client.get("/api/v1/favorites", headers=auth(user_token))
        assert resp.status_code == 200
        ids = [f["parking_id"] for f in resp.json()]
        assert "parking_3" in ids

        # Remove
        resp = await client.delete("/api/v1/favorites/parking_3", headers=auth(user_token))
        assert resp.status_code == 200


# ─── Notifications ───────────────────────────────────

class TestNotifications:
    @pytest.mark.anyio
    async def test_get_notifications(self, client, user_token):
        resp = await client.get("/api/v1/notifications", headers=auth(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.anyio
    async def test_unread_count(self, client, user_token):
        resp = await client.get("/api/v1/notifications/unread-count", headers=auth(user_token))
        assert resp.status_code == 200
        assert "count" in resp.json()

    @pytest.mark.anyio
    async def test_mark_all_read(self, client, user_token):
        resp = await client.put("/api/v1/notifications/read-all", headers=auth(user_token))
        assert resp.status_code == 200


# ─── Support Tickets ─────────────────────────────────

class TestSupport:
    @pytest.mark.anyio
    async def test_create_ticket(self, client, user_token):
        resp = await client.post("/api/v1/support/tickets", headers=auth(user_token), json={
            "subject": "Test Issue",
            "message": "Something is broken",
            "category": "technical"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["subject"] == "Test Issue"
        assert data["status"] == "open"

    @pytest.mark.anyio
    async def test_list_tickets(self, client, user_token):
        resp = await client.get("/api/v1/support/tickets", headers=auth(user_token))
        assert resp.status_code == 200


# ─── IoT / Hardware ──────────────────────────────────

class TestIoT:
    @pytest.mark.anyio
    async def test_plate_detect_with_booking(self, client, user_token):
        """Test ALPR plate detection verifies against bookings."""
        # Use parking_5 with an available slot (C01 is available)
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_5",
            "slot_id": "parking_5_slot_C01",
            "vehicle_plate": "ذ ز ش 6789",
            "start_time": "2026-03-14T10:00:00",
            "end_time": "2026-03-14T14:00:00"
        })
        assert create.status_code == 200

        # Simulate ALPR entry detection
        resp = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_5",
            "plate": "ذ ز ش 6789",
            "action": "entry",
            "device_key": "esp32_parking5_key"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is True
        assert data["gate_command"] == "open"
        assert data["booking_id"] is not None

    @pytest.mark.anyio
    async def test_plate_detect_no_booking(self, client):
        """Test ALPR rejects unregistered vehicle at entry."""
        resp = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_1",
            "plate": "UNKNOWN_PLATE",
            "action": "entry",
            "device_key": "esp32_parking1_key"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is False
        assert data["gate_command"] == "none"

    @pytest.mark.anyio
    async def test_plate_detect_exit_no_booking(self, client):
        """Test exit always opens gate even without booking."""
        resp = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_1",
            "plate": "RANDOM_PLATE",
            "action": "exit",
            "device_key": "esp32_parking1_key"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["gate_command"] == "open"  # Don't trap cars

    @pytest.mark.anyio
    async def test_plate_detect_invalid_key(self, client):
        resp = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_1",
            "plate": "أ ب ج 1234",
            "action": "entry",
            "device_key": "wrong_key"
        })
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_fire_alert(self, client):
        resp = await client.post("/api/v1/iot/fire-alert", params={
            "parking_id": "parking_1",
            "message": "Smoke detected floor 2",
            "confidence": 0.92,
            "device_key": "esp32_parking1_key"
        })
        assert resp.status_code == 200
        assert "alert_id" in resp.json()

    @pytest.mark.anyio
    async def test_theft_alert(self, client):
        resp = await client.post("/api/v1/iot/theft-alert", params={
            "parking_id": "parking_2",
            "message": "Weapon detected",
            "confidence": 0.85,
            "weapon_type": "knife",
            "device_key": "esp32_parking2_key"
        })
        assert resp.status_code == 200
        assert "alert_id" in resp.json()

    @pytest.mark.anyio
    async def test_slot_update(self, client):
        resp = await client.post("/api/v1/iot/slot-update", params={
            "parking_id": "parking_1",
            "slot_number": "A01",
            "status": "available",
            "device_key": "esp32_parking1_key"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "available"

    @pytest.mark.anyio
    async def test_gate_control(self, client):
        resp = await client.post("/api/v1/iot/gate-control", params={
            "parking_id": "parking_1",
            "gate_type": "entry",
            "action": "open",
            "device_key": "esp32_parking1_key"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ─── Admin Endpoints ─────────────────────────────────

class TestAdmin:
    @pytest.mark.anyio
    async def test_dashboard(self, client, admin_token):
        resp = await client.get("/api/v1/admin/dashboard", headers=auth(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_parkings" in data
        assert "total_slots" in data
        assert "available_slots" in data
        assert "pending_alerts" in data

    @pytest.mark.anyio
    async def test_dashboard_unauthorized(self, client, user_token):
        """Regular user cannot access admin dashboard."""
        resp = await client.get("/api/v1/admin/dashboard", headers=auth(user_token))
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_list_users(self, client, admin_token):
        resp = await client.get("/api/v1/admin/users", headers=auth(admin_token))
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) >= 5
        for u in users:
            assert "password_hash" not in u

    @pytest.mark.anyio
    async def test_get_user(self, client, admin_token):
        resp = await client.get("/api/v1/admin/users/user_amira", headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "amira@gmail.com"

    @pytest.mark.anyio
    async def test_all_bookings(self, client, admin_token):
        resp = await client.get("/api/v1/admin/bookings", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_alerts(self, client, admin_token):
        resp = await client.get("/api/v1/admin/alerts", headers=auth(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.anyio
    async def test_alert_acknowledge_resolve(self, client, admin_token):
        # Get an active alert
        alerts = await client.get("/api/v1/admin/alerts", headers=auth(admin_token), params={"status": "active"})
        if alerts.json():
            alert_id = alerts.json()[0]["id"]
            # Acknowledge
            ack = await client.put(f"/api/v1/admin/alerts/{alert_id}/acknowledge", headers=auth(admin_token))
            assert ack.status_code == 200
            assert ack.json()["status"] == "acknowledged"
            # Resolve
            res = await client.put(f"/api/v1/admin/alerts/{alert_id}/resolve", headers=auth(admin_token))
            assert res.status_code == 200
            assert res.json()["status"] == "resolved"

    @pytest.mark.anyio
    async def test_vehicle_logs(self, client, admin_token):
        resp = await client.get("/api/v1/admin/vehicles/logs", headers=auth(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.anyio
    async def test_vehicle_logs_filter(self, client, admin_token):
        resp = await client.get("/api/v1/admin/vehicles/logs", headers=auth(admin_token), params={
            "parking_id": "parking_1",
            "action": "entry"
        })
        assert resp.status_code == 200
        for log in resp.json():
            assert log["parking_id"] == "parking_1"
            assert log["action"] == "entry"

    @pytest.mark.anyio
    async def test_send_notification(self, client, admin_token):
        resp = await client.post("/api/v1/admin/notifications/send", headers=auth(admin_token), json={
            "user_id": "user_amira",
            "title": "Test Notification",
            "message": "This is a test",
            "notification_type": "system"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.anyio
    async def test_broadcast_notification(self, client, admin_token):
        resp = await client.post("/api/v1/admin/notifications/send", headers=auth(admin_token), json={
            "title": "System Update",
            "message": "Maintenance scheduled"
        })
        assert resp.status_code == 200
        assert "broadcast" in resp.json()["message"]

    @pytest.mark.anyio
    async def test_support_tickets_admin(self, client, admin_token):
        resp = await client.get("/api/v1/admin/support/tickets", headers=auth(admin_token))
        assert resp.status_code == 200


# ─── Admin Parking CRUD ──────────────────────────────

class TestAdminParkingCRUD:
    @pytest.mark.anyio
    async def test_create_parking(self, client, admin_token):
        resp = await client.post("/api/v1/admin/parkings", headers=auth(admin_token), json={
            "name": "Test New Parking",
            "description": "Created by unit test",
            "latitude": 30.1,
            "longitude": 31.3,
            "address": "Test Address, Cairo",
            "city": "Cairo",
            "parking_type": "covered",
            "total_slots": 20,
            "rate_per_hour": 25.0,
            "amenities": ["cctv", "security"],
            "is_24_7": True
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test New Parking"
        assert data["total_slots"] == 20
        assert data["available_slots"] == 20
        assert data["rate_per_hour"] == 25.0

    @pytest.mark.anyio
    async def test_update_parking(self, client, admin_token):
        resp = await client.put("/api/v1/admin/parkings/parking_1", headers=auth(admin_token), json={
            "rate_per_hour": 22.0,
            "amenities": ["covered", "cctv", "ev_charger", "24_7", "security", "valet"]
        })
        assert resp.status_code == 200
        assert resp.json()["rate_per_hour"] == 22.0
        assert "valet" in resp.json()["amenities"]

    @pytest.mark.anyio
    async def test_update_parking_not_found(self, client, admin_token):
        resp = await client.put("/api/v1/admin/parkings/nonexistent", headers=auth(admin_token), json={
            "name": "Nope"
        })
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_parking(self, client, admin_token):
        # Create one to delete
        create = await client.post("/api/v1/admin/parkings", headers=auth(admin_token), json={
            "name": "To Delete",
            "latitude": 30.0,
            "longitude": 31.0,
            "address": "Temp",
            "total_slots": 5,
            "rate_per_hour": 10.0
        })
        pid = create.json()["id"]
        resp = await client.delete(f"/api/v1/admin/parkings/{pid}", headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.anyio
    async def test_admin_get_slots(self, client, admin_token):
        resp = await client.get("/api/v1/admin/parkings/parking_1/slots", headers=auth(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ─── Admin User Management ───────────────────────────

class TestAdminUserManagement:
    @pytest.mark.anyio
    async def test_suspend_user(self, client, admin_token):
        resp = await client.put("/api/v1/admin/users/user_omar/suspend", headers=auth(admin_token), json={
            "is_active": False,
            "reason": "Suspicious activity"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"
        assert resp.json()["is_active"] is False

    @pytest.mark.anyio
    async def test_activate_user(self, client, admin_token):
        resp = await client.put("/api/v1/admin/users/user_omar/suspend", headers=auth(admin_token), json={
            "is_active": True
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "activated"

    @pytest.mark.anyio
    async def test_cannot_suspend_admin(self, client, admin_token):
        resp = await client.put("/api/v1/admin/users/admin_user/suspend", headers=auth(admin_token), json={
            "is_active": False
        })
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_delete_user(self, client, admin_token):
        # Register a throwaway user first
        reg = await client.post("/api/v1/auth/register", json={
            "email": "throwaway@test.com",
            "name": "Throwaway",
            "password": "test123"
        })
        uid = reg.json()["user"]["id"]

        resp = await client.delete(f"/api/v1/admin/users/{uid}", headers=auth(admin_token))
        assert resp.status_code == 200

        # Verify deleted
        resp = await client.get(f"/api/v1/admin/users/{uid}", headers=auth(admin_token))
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_cannot_delete_admin(self, client, admin_token):
        resp = await client.delete("/api/v1/admin/users/admin_user", headers=auth(admin_token))
        assert resp.status_code == 400


# ─── Full ALPR → Check-in → Check-out Flow ──────────

class TestALPRFullFlow:
    @pytest.mark.anyio
    async def test_full_parking_flow(self, client, user_token):
        """
        Complete flow: Book → ALPR Entry (auto check-in) → ALPR Exit (auto check-out)
        """
        # Use a unique plate and slot that no other test touches
        test_plate = "ص ض ط 0123"

        # 1. User books a slot
        create = await client.post("/api/v1/bookings", headers=auth(user_token), json={
            "parking_id": "parking_1",
            "slot_id": "parking_1_slot_C01",
            "vehicle_plate": test_plate,
            "start_time": "2026-03-14T08:00:00",
            "end_time": "2026-03-14T12:00:00"
        })
        assert create.status_code == 200
        booking_id = create.json()["id"]
        assert create.json()["status"] == "confirmed"

        # 2. Car arrives at gate → ALPR detects plate → auto check-in
        entry = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_1",
            "plate": test_plate,
            "action": "entry",
            "gate": "Gate A",
            "device_key": "esp32_parking1_key"
        })
        assert entry.status_code == 200
        assert entry.json()["verified"] is True
        assert entry.json()["gate_command"] == "open"
        assert entry.json()["booking_id"] == booking_id

        # 3. Verify booking is now active
        booking = await client.get(f"/api/v1/bookings/{booking_id}", headers=auth(user_token))
        assert booking.json()["status"] == "active"

        # 4. Car leaves → ALPR detects plate → auto check-out
        exit_resp = await client.post("/api/v1/iot/plate-detect", params={
            "parking_id": "parking_1",
            "plate": test_plate,
            "action": "exit",
            "gate": "Gate B",
            "device_key": "esp32_parking1_key"
        })
        assert exit_resp.status_code == 200
        assert exit_resp.json()["verified"] is True
        assert exit_resp.json()["gate_command"] == "open"

        # 5. Verify booking is completed
        booking = await client.get(f"/api/v1/bookings/{booking_id}", headers=auth(user_token))
        assert booking.json()["status"] == "completed"
