# Parkify API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8000`
**Interactive Docs:** `http://localhost:8000/docs`
**Admin Dashboard:** `http://localhost:8000/dashboard`

## Demo Accounts

| Role  | Email               | Password  |
|-------|---------------------|-----------|
| Admin | admin@parkify.com   | admin123  |
| User  | amira@gmail.com     | user123   |
| User  | ahmed@gmail.com     | user123   |
| User  | sara@gmail.com      | user123   |
| User  | omar@gmail.com      | user123   |

## Authentication

All protected endpoints require a **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

IoT/Hardware endpoints use a `device_key` query parameter instead.

---

## Table of Contents

1. [Root & Health](#1-root--health)
2. [Authentication](#2-authentication)
3. [Users & Profile](#3-users--profile)
4. [Cars](#4-cars)
5. [Payment Methods](#5-payment-methods)
6. [Parkings](#6-parkings)
7. [Bookings](#7-bookings)
8. [Favorites](#8-favorites)
9. [Notifications](#9-notifications)
10. [Support Tickets](#10-support-tickets)
11. [Admin - Dashboard & Stats](#11-admin---dashboard--stats)
12. [Admin - Parking Management (CRUD)](#12-admin---parking-management-crud)
13. [Admin - User Management](#13-admin---user-management)
14. [Admin - Bookings Management](#14-admin---bookings-management)
15. [Admin - Alerts Management](#15-admin---alerts-management)
16. [Admin - Vehicle Logs (ALPR)](#16-admin---vehicle-logs-alpr)
17. [Admin - Gate Control](#17-admin---gate-control)
18. [Admin - Notifications](#18-admin---notifications)
19. [Admin - Support Tickets](#19-admin---support-tickets)
20. [IoT / Hardware Endpoints](#20-iot--hardware-endpoints)
21. [WebSocket Endpoints](#21-websocket-endpoints)
22. [Data Models Reference](#22-data-models-reference)

---

## 1. Root & Health

### `GET /`

Returns API welcome info and links.

**Auth:** None

**Response:**
```json
{
  "message": "Welcome to Parkify API",
  "version": "3.0.0",
  "docs": "/docs",
  "admin_dashboard": "/dashboard",
  "demo_accounts": {
    "admin": "admin@parkify.com / admin123",
    "user": "user@parkify.com / user123"
  }
}
```

---

### `GET /health`

Health check for monitoring.

**Auth:** None

**Response:**
```json
{
  "status": "healthy",
  "service": "parkify-api",
  "version": "3.0.0"
}
```

---

## 2. Authentication

### `POST /api/v1/auth/register`

Register a new user account.

**Auth:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword",
  "phone": "+20 1234567890"  // optional
}
```

**Response:** `TokenResponse` — returns access token, refresh token, and user info.

**What it does:** Creates a new user in the system, hashes the password with bcrypt, generates JWT access/refresh tokens, and returns them so the user is immediately logged in.

---

### `POST /api/v1/auth/login`

Login with email and password.

**Auth:** None

**Request Body:**
```json
{
  "email": "amira@gmail.com",
  "password": "user123"
}
```

**Response:** `TokenResponse`

**What it does:** Verifies the email exists and password matches the stored bcrypt hash. If valid, generates and returns JWT access token (30 min expiry) and refresh token (7 day expiry).

---

### `POST /api/v1/auth/refresh`

Refresh an expired access token.

**Auth:** None

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `TokenResponse`

**What it does:** Validates the refresh token, extracts the user ID, and issues a new access/refresh token pair.

---

### `POST /api/v1/auth/social`

Login or register via social provider (Google, Facebook, Apple).

**Auth:** None

**Request Body:**
```json
{
  "provider": "google",
  "token": "social_provider_token",
  "name": "John Doe",
  "email": "john@gmail.com"
}
```

**Response:** `TokenResponse`

**What it does:** Checks if a user with this email already exists — if yes, logs them in. If not, creates a new account linked to the social provider and returns tokens.

---

### `POST /api/v1/auth/forgot-password/email`

Send a 6-digit password reset code to the user's email.

**Auth:** None

**Request Body:**
```json
{
  "email": "amira@gmail.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reset code sent to email",
  "code": "123456"
}
```

**What it does:** Looks up the user by email, generates a random 6-digit code with 15 min expiry, and stores it. In production, this would send an actual email; in demo mode, the code is returned in the response.

---

### `POST /api/v1/auth/forgot-password/phone`

Send a 6-digit password reset code to the user's phone.

**Auth:** None

**Request Body:**
```json
{
  "phone": "+20 0967 834 888"
}
```

**Response:** Same as email version.

**What it does:** Same as email version but looks up user by phone number.

---

### `POST /api/v1/auth/verify-code`

Verify an OTP code sent to email or phone.

**Auth:** None

**Request Body:**
```json
{
  "email": "amira@gmail.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Code verified"
}
```

**What it does:** Checks the stored code against the provided one, verifies it hasn't expired (10 min window), and marks it as verified.

---

### `POST /api/v1/auth/resend-code`

Resend a verification code.

**Auth:** None

**Request Body:**
```json
{
  "email": "amira@gmail.com"
}
```

**What it does:** Generates a new 6-digit code and replaces the old one. Resets the expiry timer.

---

### `POST /api/v1/auth/reset-password`

Reset the user's password using a verified code.

**Auth:** None

**Request Body:**
```json
{
  "email": "amira@gmail.com",
  "code": "123456",
  "new_password": "newpassword123"
}
```

**What it does:** Verifies the reset code is valid, hashes the new password with bcrypt, updates the user's stored password hash, and clears the reset code.

---

## 3. Users & Profile

### `GET /api/v1/users/profile`

Get the current user's profile.

**Auth:** Bearer Token (User)

**Response:** `UserProfileResponse`
```json
{
  "id": "user_amira",
  "email": "amira@gmail.com",
  "first_name": "Amira",
  "last_name": "Elmohndes",
  "name": "Amira Elmohndes",
  "phone": "+20 0967 834 888",
  "gender": "female",
  "address": "New Cairo, Egypt",
  "profile_photo": null,
  "role": "user",
  "is_active": true,
  "created_at": "2024-06-15T10:30:00"
}
```

**What it does:** Decodes the JWT token to get the user ID, fetches the user record, and returns profile info (excluding password hash).

---

### `PUT /api/v1/users/profile`

Update the current user's profile.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "first_name": "Amira",
  "last_name": "Elmohndes",
  "phone": "+20 1111111111",
  "address": "Maadi, Cairo",
  "email": "newemail@gmail.com",
  "gender": "female"
}
```

All fields are optional — only send what you want to update.

**What it does:** Updates only the provided fields on the user record. Automatically recalculates the `name` field from first_name + last_name.

---

### `POST /api/v1/users/profile/complete`

Complete initial profile setup (after registration).

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "first_name": "Amira",
  "last_name": "Elmohndes",
  "gender": "female",
  "phone": "+20 0967 834 888",
  "address": "New Cairo, Egypt",
  "car_plate": "أ ب ج 1234",
  "car_model": "Toyota Corolla"
}
```

**What it does:** Sets the user's first name, last name, gender, phone, and address. If `car_plate` is provided, creates a car entry and adds it to the user's car list as the default car.

---

### `PUT /api/v1/users/change-password`

Change the current user's password.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "current_password": "user123",
  "new_password": "newsecurepass"
}
```

**What it does:** Verifies the current password matches the stored hash, then updates to the new hashed password. Returns 400 if current password is wrong.

---

## 4. Cars

### `GET /api/v1/users/cars`

List all cars registered to the current user.

**Auth:** Bearer Token (User)

**Response:** `List[CarResponse]`
```json
[
  {
    "id": "car_1",
    "license_plate": "أ ب ج 1234",
    "make": "Toyota",
    "model": "Corolla",
    "color": "White",
    "is_default": true
  }
]
```

**What it does:** Returns the `cars` array from the user's record.

---

### `POST /api/v1/users/cars`

Add a new car.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "license_plate": "ت ث خ 5678",
  "make": "Hyundai",
  "model": "Elantra",
  "color": "Silver",
  "is_default": false
}
```

**What it does:** Creates a car with a unique ID, appends it to the user's car list. If it's the first car or `is_default: true`, sets it as the default (and clears the flag on other cars).

---

### `PUT /api/v1/users/cars/{car_id}`

Update a car's details.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "license_plate": "New Plate",
  "make": "BMW",
  "model": "X3",
  "color": "Black"
}
```

All fields optional.

**What it does:** Finds the car by ID in the user's car list and updates the provided fields.

---

### `DELETE /api/v1/users/cars/{car_id}`

Remove a car.

**Auth:** Bearer Token (User)

**What it does:** Removes the car from the user's car list. If it was the default car, automatically sets the first remaining car as default.

---

### `PUT /api/v1/users/cars/{car_id}/default`

Set a car as the default.

**Auth:** Bearer Token (User)

**What it does:** Sets `is_default: true` on the target car and `is_default: false` on all others.

---

## 5. Payment Methods

### `GET /api/v1/users/payment-methods`

List all payment methods.

**Auth:** Bearer Token (User)

**Response:** `List[PaymentMethodResponse]`
```json
[
  {
    "id": "pm_1",
    "method_type": "card",
    "last_four": "4242",
    "card_holder": "Amira Elmohndes",
    "expiry": "12/26",
    "is_default": true
  }
]
```

---

### `POST /api/v1/users/payment-methods`

Add a new payment method.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "method_type": "card",
  "card_number": "4111111111114242",
  "card_holder": "Amira Elmohndes",
  "expiry_month": 12,
  "expiry_year": 2026,
  "is_default": true
}
```

Supported `method_type`: `"card"`, `"apple_pay"`, `"google_pay"`, `"cash"`

**What it does:** Stores only the last 4 digits of the card number (never the full number). Sets as default if first method or explicitly requested.

---

### `DELETE /api/v1/users/payment-methods/{method_id}`

Remove a payment method.

**Auth:** Bearer Token (User)

**What it does:** Removes the payment method. If it was default, auto-promotes the first remaining method.

---

### `PUT /api/v1/users/payment-methods/{method_id}/default`

Set a payment method as default.

**Auth:** Bearer Token (User)

**What it does:** Sets `is_default: true` on target, `false` on all others.

---

## 6. Parkings

### `GET /api/v1/parkings`

List all active parkings.

**Auth:** Bearer Token (User)

**Response:** `List[ParkingResponse]` — each includes `is_favorited` flag for the current user.

**What it does:** Returns all parkings from the database, enriched with whether the current user has favorited each one.

---

### `GET /api/v1/parkings/search`

Search for nearby parkings by GPS coordinates.

**Auth:** Bearer Token (User)

**Query Parameters:**
| Parameter   | Type   | Required | Default    | Description                        |
|-------------|--------|----------|------------|------------------------------------|
| latitude    | float  | Yes      | —          | User's latitude                    |
| longitude   | float  | Yes      | —          | User's longitude                   |
| radius_km   | float  | No       | 10         | Search radius in kilometers        |
| sort_by     | string | No       | "distance" | Sort: "distance", "price", "rating"|

**Response:** `List[ParkingResponse]` — includes `distance_meters` and `walking_time_minutes`.

**What it does:** Calculates the Haversine distance between the user's location and each parking. Filters by radius, sorts by chosen criteria, and estimates walking time at 80m/min.

---

### `GET /api/v1/parkings/search-by-name`

Search parkings by name, description, address, or city.

**Auth:** Bearer Token (User)

**Query Parameters:**
| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| q         | string | Yes      | Search text (min 1 char) |

**What it does:** Case-insensitive text search across parking name, description, address, and city fields.

---

### `POST /api/v1/parkings/filter`

Advanced multi-criteria filtering.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "latitude": 30.0285,
  "longitude": 31.4085,
  "radius_km": 10.0,
  "min_price": 10.0,
  "max_price": 25.0,
  "parking_type": "covered",
  "sort_by": "price",
  "amenities": ["cctv", "ev_charger"],
  "available_only": true
}
```

All fields optional.

**What it does:** Applies all provided filters: location radius, price range, parking type, required amenities, and availability. Sorts results by distance, price, or rating.

---

### `GET /api/v1/parkings/filter`

Same as POST filter but via query parameters (for GET-friendly clients).

**Auth:** Bearer Token (User)

**Query Parameters:**
| Parameter      | Type   | Default    |
|----------------|--------|------------|
| latitude       | float  | None       |
| longitude      | float  | None       |
| radius_km      | float  | 10         |
| min_price      | float  | None       |
| max_price      | float  | None       |
| parking_type   | string | None       |
| sort_by        | string | "distance" |
| available_only | bool   | true       |

---

### `GET /api/v1/parkings/{parking_id}`

Get detailed info for a specific parking.

**Auth:** Bearer Token (User)

**Response:** `ParkingResponse`

**What it does:** Returns full parking details including slot counts, rates, amenities, rating, and favorite status.

---

### `GET /api/v1/parkings/{parking_id}/slots`

Get all slots for a parking.

**Auth:** Bearer Token (User)

**Response:** `List[ParkingSlot]` — sorted by floor and slot number.
```json
[
  {
    "id": "parking_1_slot_A01",
    "parking_id": "parking_1",
    "slot_number": "A01",
    "floor": 1,
    "section": "A",
    "status": "available",
    "is_handicap": true,
    "is_ev_charging": true,
    "current_vehicle_plate": null
  }
]
```

**What it does:** Returns all slots for the parking, sorted by floor then slot number. Shows status (available/occupied/reserved), handicap/EV flags.

---

### `GET /api/v1/parkings/{parking_id}/slots/available`

Get only available slots for a parking.

**Auth:** Bearer Token (User)

**Response:** `List[ParkingSlot]` — only slots with `status: "available"`.

**What it does:** Same as above but filtered to only available slots. Useful for the mobile app to show where the user can park.

---

### `POST /api/v1/parkings/{parking_id}/watch`

Subscribe to availability notifications for a full parking.

**Auth:** Bearer Token (User)

**Response:**
```json
{
  "success": true,
  "message": "You will be notified when a spot becomes available"
}
```

**What it does:** Adds the user to the parking's watcher list. When a slot becomes available (via check-out, ALPR exit, or sensor update), all watchers receive a push notification and are auto-unsubscribed.

---

### `DELETE /api/v1/parkings/{parking_id}/watch`

Unsubscribe from availability notifications.

**Auth:** Bearer Token (User)

**What it does:** Removes the user from the parking's watcher list.

---

### `GET /api/v1/parkings/{parking_id}/watch`

Check if you're watching this parking.

**Auth:** Bearer Token (User)

**Response:**
```json
{
  "is_watching": true
}
```

---

## 7. Bookings

### `POST /api/v1/bookings`

Create a new parking reservation.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "parking_id": "parking_1",
  "slot_id": "parking_1_slot_A05",
  "vehicle_plate": "أ ب ج 1234",
  "start_time": "2026-03-13T10:00:00",
  "end_time": "2026-03-13T12:00:00",
  "payment_method": "card"
}
```

**Response:** `BookingResponse`

**What it does:**
1. Validates parking and slot exist and slot is available
2. Calculates price: `hours * rate_per_hour + 5% fees`
3. Creates booking with status `confirmed`, payment status `completed`
4. Marks the slot as `reserved` and decrements available slot count
5. Creates booking confirmation and payment confirmation notifications

---

### `GET /api/v1/bookings`

Get all bookings for the current user.

**Auth:** Bearer Token (User)

**Response:** `List[BookingResponse]`

---

### `GET /api/v1/bookings/active`

Get the current active booking (if any).

**Auth:** Bearer Token (User)

**Response:** `ActiveBookingResponse` or `null`
```json
{
  "id": "booking_abc123",
  "parking_name": "Cairo Festival City Mall",
  "parking_address": "New Cairo, Cairo Governorate",
  "slot_id": "parking_1_slot_A05",
  "slot_number": "A05",
  "floor": 1,
  "remaining_time_seconds": 3600,
  "start_time": "2026-03-13T10:00:00",
  "end_time": "2026-03-13T12:00:00"
}
```

**What it does:** Finds a booking with status `confirmed` or `active` where `end_time` hasn't passed. Calculates remaining time in seconds.

---

### `GET /api/v1/bookings/history`

Get past bookings (completed and cancelled).

**Auth:** Bearer Token (User)

**Response:** `List[BookingResponse]` — only bookings with status `completed` or `cancelled`.

---

### `GET /api/v1/bookings/{booking_id}`

Get a specific booking's details.

**Auth:** Bearer Token (User)

**Response:** `BookingResponse`

**What it does:** Returns booking details. Returns 404 if the booking doesn't exist or doesn't belong to the current user.

---

### `GET /api/v1/bookings/{booking_id}/qr`

Get QR code data for gate entry/exit.

**Auth:** Bearer Token (User)

**Response:** `BookingQRResponse`
```json
{
  "booking_id": "booking_abc123",
  "qr_data": "{\"booking_id\":\"booking_abc123\",\"parking_id\":\"parking_1\",\"slot\":\"A05\",\"plate\":\"أ ب ج 1234\",\"valid_from\":\"...\",\"valid_until\":\"...\",\"checksum\":\"a1b2c3d4\"}",
  "parking_name": "Cairo Festival City Mall",
  "slot_number": "A05",
  "start_time": "2026-03-13T10:00:00",
  "end_time": "2026-03-13T12:00:00",
  "vehicle_plate": "أ ب ج 1234"
}
```

**What it does:** Generates a JSON string containing booking details and an MD5 checksum. The mobile app renders this as a QR code that can be scanned at the gate.

---

### `POST /api/v1/bookings/{booking_id}/check-in`

Manually check in to parking (e.g., scan QR at gate).

**Auth:** Bearer Token (User)

**Response:** `BookingResponse` with status `active`

**What it does:**
1. Validates booking belongs to user and is in `confirmed` status
2. Changes status to `active`
3. Records actual entry time
4. Marks the slot as `occupied` and sets `current_vehicle_plate`
5. Sends "Welcome! You've Checked In" notification

**Note:** This is also triggered automatically by ALPR plate detection at entry.

---

### `POST /api/v1/bookings/{booking_id}/check-out`

Manually check out from parking.

**Auth:** Bearer Token (User)

**Response:** `BookingResponse` with status `completed`

**What it does:**
1. Validates booking is in `active` status
2. Changes status to `completed`, records actual exit time
3. **Calculates overstay charges**: if actual duration > booked duration, extra hours are charged at the parking's hourly rate + 5% fees
4. Frees the slot (status back to `available`, clears vehicle plate)
5. Increments available slot count
6. Sends "Trip Complete!" notification with final amount

**Note:** This is also triggered automatically by ALPR plate detection at exit.

---

### `POST /api/v1/bookings/{booking_id}/cancel`

Cancel a booking.

**Auth:** Bearer Token (User)

**Response:** `BookingResponse` with status `cancelled`

**What it does:**
1. Only works for `pending` or `confirmed` bookings
2. Sets status to `cancelled`, payment to `refunded`
3. Frees the slot and increments available count
4. Sends cancellation notification with refund info

---

### `POST /api/v1/bookings/{booking_id}/extend`

Extend an active booking.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "additional_hours": 2.0
}
```

**Response:** `BookingResponse` with updated end_time and price.

**What it does:** Adds hours to the end_time, recalculates the total price (extra hours * rate + 5% fees added to existing amount).

---

## 8. Favorites

### `GET /api/v1/favorites`

Get all favorited parkings.

**Auth:** Bearer Token (User)

**Response:** `List[FavoriteResponse]` — each includes full parking details.

---

### `POST /api/v1/favorites/{parking_id}`

Add a parking to favorites.

**Auth:** Bearer Token (User)

**Response:** `FavoriteResponse`

**What it does:** Adds the parking_id to the user's favorites list. If already favorited, it's a no-op.

---

### `DELETE /api/v1/favorites/{parking_id}`

Remove a parking from favorites.

**Auth:** Bearer Token (User)

---

### `GET /api/v1/favorites/{parking_id}/check`

Check if a parking is favorited.

**Auth:** Bearer Token (User)

**Response:**
```json
{
  "is_favorited": true
}
```

---

## 9. Notifications

### `GET /api/v1/notifications`

Get all notifications for the current user.

**Auth:** Bearer Token (User)

**Response:** `List[NotificationResponse]` — sorted by created_at (newest first), unread first.

```json
[
  {
    "id": "notif_1",
    "user_id": "user_amira",
    "title": "Booking Successful!",
    "message": "You have successfully booked a slot...",
    "notification_type": "booking",
    "is_read": false,
    "data": {"booking_id": "booking_demo1"},
    "created_at": "2026-03-13T10:00:00"
  }
]
```

**Notification types:** `booking`, `payment`, `promo`, `security`, `system`, `alert`

---

### `GET /api/v1/notifications/unread-count`

Get count of unread notifications.

**Auth:** Bearer Token (User)

**Response:**
```json
{
  "count": 3
}
```

---

### `PUT /api/v1/notifications/{notification_id}/read`

Mark a notification as read.

**Auth:** Bearer Token (User)

---

### `PUT /api/v1/notifications/read-all`

Mark all notifications as read.

**Auth:** Bearer Token (User)

**Response:**
```json
{
  "success": true,
  "marked_count": 5
}
```

---

### `DELETE /api/v1/notifications/{notification_id}`

Delete a notification.

**Auth:** Bearer Token (User)

---

## 10. Support Tickets

### `POST /api/v1/support/tickets`

Create a new support ticket.

**Auth:** Bearer Token (User)

**Request Body:**
```json
{
  "subject": "Payment issue",
  "message": "I was charged twice for my booking.",
  "category": "payment"
}
```

Categories: `"general"`, `"booking"`, `"payment"`, `"technical"`

**What it does:** Creates a ticket with status `open` and timestamps.

---

### `GET /api/v1/support/tickets`

Get all support tickets for the current user.

**Auth:** Bearer Token (User)

**Response:** `List[SupportTicketResponse]` — sorted newest first.

---

### `GET /api/v1/support/tickets/{ticket_id}`

Get a specific ticket.

**Auth:** Bearer Token (User)

---

## 11. Admin - Dashboard & Stats

### `GET /api/v1/admin/dashboard`

Get real-time dashboard statistics.

**Auth:** Bearer Token (Admin)

**Response:** `DashboardStats`
```json
{
  "total_parkings": 7,
  "total_slots": 910,
  "available_slots": 552,
  "occupied_slots": 358,
  "total_users": 5,
  "active_bookings": 2,
  "today_bookings": 8,
  "today_revenue": 1250.50,
  "pending_alerts": 2,
  "currency": "EGP"
}
```

**What it does:** Aggregates real-time stats across all parkings: total/available/occupied slots, user count, active bookings, revenue from completed payments, and active alert count.

---

## 12. Admin - Parking Management (CRUD)

### `GET /api/v1/admin/parkings`

Get all parkings with full details.

**Auth:** Bearer Token (Admin)

**Response:** `List[ParkingResponse]`

---

### `POST /api/v1/admin/parkings`

Create a new parking location.

**Auth:** Bearer Token (Admin)

**Request Body:**
```json
{
  "name": "New Smart Parking",
  "description": "Modern parking with full automation",
  "latitude": 30.05,
  "longitude": 31.35,
  "address": "Nasr City, Cairo",
  "city": "Cairo",
  "country": "Egypt",
  "parking_type": "multi_level",
  "total_slots": 50,
  "rate_per_hour": 20.0,
  "currency": "EGP",
  "amenities": ["covered", "cctv", "ev_charger", "security"],
  "is_24_7": true
}
```

**Response:** `ParkingResponse`

**What it does:**
1. Creates a new parking with a unique ID
2. Auto-generates all slots with floor/section/number assignments (20 slots per floor, 3 sections A/B/C per floor)
3. Marks every 10th slot as handicap, every 15th as EV charging
4. All slots start as `available`

---

### `PUT /api/v1/admin/parkings/{parking_id}`

Update parking details.

**Auth:** Bearer Token (Admin)

**Request Body:**
```json
{
  "name": "Updated Name",
  "rate_per_hour": 25.0,
  "amenities": ["covered", "cctv", "ev_charger"],
  "is_active": false
}
```

All fields optional — only send what you want to update.

**What it does:** Updates only the provided fields. Can be used to change rates, amenities, hours, address, or deactivate a parking.

---

### `DELETE /api/v1/admin/parkings/{parking_id}`

Deactivate a parking (soft delete).

**Auth:** Bearer Token (Admin)

**Response:**
```json
{
  "success": true,
  "message": "Parking parking_1 deactivated"
}
```

**What it does:** Sets `is_active: false` on the parking. It won't appear in user searches but data is preserved.

---

### `GET /api/v1/admin/parkings/{parking_id}/slots`

Get all slots for a specific parking.

**Auth:** Bearer Token (Admin)

**Response:** `List[ParkingSlot]`

---

## 13. Admin - User Management

### `GET /api/v1/admin/users`

List all users.

**Auth:** Bearer Token (Admin)

**Response:** List of user objects (password hashes excluded).

---

### `GET /api/v1/admin/users/{user_id}`

Get a specific user's details.

**Auth:** Bearer Token (Admin)

**Response:** User object with all fields except password hash.

---

### `PUT /api/v1/admin/users/{user_id}/suspend`

Suspend or reactivate a user account.

**Auth:** Bearer Token (Admin)

**Request Body:**
```json
{
  "is_active": false,
  "reason": "Suspicious activity detected by theft detection system"
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_amira",
  "status": "suspended",
  "is_active": false
}
```

**What it does:**
1. Prevents modification of admin accounts
2. Sets the user's `is_active` flag
3. If suspending with a reason, sends a "Account Suspended" security notification to the user
4. Suspended users cannot log in

---

### `DELETE /api/v1/admin/users/{user_id}`

Permanently delete a user account.

**Auth:** Bearer Token (Admin)

**Response:**
```json
{
  "success": true,
  "message": "User user_amira deleted"
}
```

**What it does:** Removes the user from the system entirely. Admin accounts are protected and cannot be deleted.

---

## 14. Admin - Bookings Management

### `GET /api/v1/admin/bookings`

Get all bookings (system-wide).

**Auth:** Bearer Token (Admin)

**Query Parameters:**
| Parameter | Type   | Required | Description                              |
|-----------|--------|----------|------------------------------------------|
| status    | string | No       | Filter: pending, confirmed, active, completed, cancelled |

**Response:** List of booking objects, sorted newest first.

---

## 15. Admin - Alerts Management

### `GET /api/v1/admin/alerts`

Get all system alerts.

**Auth:** Bearer Token (Admin)

**Query Parameters:**
| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| status    | string | No       | Filter: active, acknowledged, resolved |

**Response:** `List[AlertResponse]` — sorted newest first.

```json
[
  {
    "id": "alert_1",
    "parking_id": "parking_1",
    "parking_name": "Cairo Festival City Mall",
    "alert_type": "fire",
    "severity": "critical",
    "message": "Smoke detected in Section B, Floor 2.",
    "status": "active",
    "created_at": "2026-03-13T10:00:00",
    "resolved_at": null,
    "resolved_by": null
  }
]
```

**Alert types:** `fire`, `theft`, `system`, `gate`, `security`
**Severity levels:** `low`, `medium`, `high`, `critical`

---

### `GET /api/v1/admin/alerts/{alert_id}`

Get a specific alert.

**Auth:** Bearer Token (Admin)

---

### `PUT /api/v1/admin/alerts/{alert_id}/acknowledge`

Acknowledge an alert (mark as seen).

**Auth:** Bearer Token (Admin)

**What it does:** Changes alert status from `active` → `acknowledged`. Indicates an admin is aware and investigating.

---

### `PUT /api/v1/admin/alerts/{alert_id}/resolve`

Resolve an alert.

**Auth:** Bearer Token (Admin)

**What it does:** Changes status to `resolved`, records `resolved_at` timestamp and `resolved_by` admin ID.

---

## 16. Admin - Vehicle Logs (ALPR)

### `GET /api/v1/admin/vehicles/logs`

Get vehicle entry/exit logs from the ALPR system.

**Auth:** Bearer Token (Admin)

**Query Parameters:**
| Parameter  | Type   | Required | Default | Description            |
|------------|--------|----------|---------|------------------------|
| parking_id | string | No       | —       | Filter by parking      |
| action     | string | No       | —       | Filter: "entry" or "exit" |
| limit      | int    | No       | 50      | Max results (1-200)    |

**Response:** `List[VehicleLogResponse]`
```json
[
  {
    "id": "vlog_1",
    "parking_id": "parking_1",
    "parking_name": "Cairo Festival City Mall",
    "vehicle_plate": "أ ب ج 1234",
    "action": "entry",
    "gate": "Gate A",
    "timestamp": "2026-03-13T10:30:00",
    "plate_image": null,
    "confidence": 0.95
  }
]
```

---

## 17. Admin - Gate Control

### `POST /api/v1/admin/gates/{parking_id}/control`

Manually open/close a parking gate.

**Auth:** Bearer Token (Admin)

**Request Body:**
```json
{
  "gate_type": "entry",
  "action": "open",
  "reason": "Manual override for maintenance"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Gate entry open sent",
  "parking_id": "parking_1"
}
```

**What it does:** Sends a gate command. In a full deployment, this would forward the command via WebSocket to the ESP32 controller at the specified parking.

---

## 18. Admin - Notifications

### `POST /api/v1/admin/notifications/send`

Send a notification to a specific user or broadcast to all.

**Auth:** Bearer Token (Admin)

**Request Body:**
```json
{
  "user_id": "user_amira",
  "title": "System Maintenance",
  "message": "The system will be down for maintenance tonight.",
  "notification_type": "system"
}
```

Set `user_id` to `null` to broadcast to all users.

**Response:**
```json
{
  "success": true,
  "message": "Notification sent",
  "notification_id": "notif_abc123"
}
```

Or for broadcast:
```json
{
  "success": true,
  "message": "Notification broadcast to 5 users"
}
```

---

## 19. Admin - Support Tickets

### `GET /api/v1/admin/support/tickets`

Get all support tickets (system-wide).

**Auth:** Bearer Token (Admin)

**Response:** `List[SupportTicketResponse]` — sorted newest first.

---

### `PUT /api/v1/admin/support/tickets/{ticket_id}/status`

Update a ticket's status.

**Auth:** Bearer Token (Admin)

**Query Parameters:**
| Parameter | Type   | Required | Description                                  |
|-----------|--------|----------|----------------------------------------------|
| status    | string | Yes      | New status: open, in_progress, resolved, closed |

---

## 20. IoT / Hardware Endpoints

These endpoints are for ESP32 devices and AI detection systems. They use `device_key` authentication instead of JWT tokens.

**Valid Device Keys:**
| Parking ID | Device Key            |
|------------|-----------------------|
| parking_1  | esp32_parking1_key    |
| parking_2  | esp32_parking2_key    |
| parking_3  | esp32_parking3_key    |
| parking_4  | esp32_parking4_key    |
| parking_5  | esp32_parking5_key    |

---

### `POST /api/v1/iot/plate-detect`

ALPR plate detection with automatic booking verification and gate control.

**Auth:** device_key query parameter

**Query Parameters:**
| Parameter  | Type   | Required | Default  | Description                |
|------------|--------|----------|----------|----------------------------|
| parking_id | string | Yes      | —        | Parking location ID        |
| plate      | string | Yes      | —        | Detected license plate     |
| action     | string | No       | "entry"  | "entry" or "exit"          |
| gate       | string | No       | "Gate A" | Gate identifier            |
| confidence | float  | No       | 0.95     | ALPR confidence score      |
| device_key | string | Yes      | —        | ESP32 authentication key   |

**Response:**
```json
{
  "success": true,
  "verified": true,
  "log_id": "vlog_abc123",
  "plate": "أ ب ج 1234",
  "action": "entry",
  "gate_command": "open",
  "booking_id": "booking_abc123",
  "message": "Vehicle verified. Booking booking_abc123 checked in."
}
```

**What it does (Entry):**
1. Logs the plate detection
2. Searches for a `confirmed` booking at this parking with a matching plate
3. **Match found:** auto check-in (confirmed → active), sends gate open command to ESP32, logs entry time
4. **No match:** creates a `security` alert for admin ("Unregistered vehicle"), gate stays closed

**What it does (Exit):**
1. Logs the plate detection
2. Searches for an `active` booking at this parking with a matching plate
3. **Match found:** auto check-out (active → completed), calculates overstay charges, frees slot, sends gate open command, notifies spot watchers
4. **No match:** opens gate anyway (can't trap a car inside), alerts admin
5. Broadcasts all events to admin WebSocket channel

---

### `POST /api/v1/iot/fire-alert`

Report a fire detection event from the AI fire detection model.

**Auth:** device_key query parameter

**Query Parameters:**
| Parameter  | Type   | Required | Default          | Description            |
|------------|--------|----------|------------------|------------------------|
| parking_id | string | Yes      | —                | Parking location       |
| message    | string | No       | "Fire detected"  | Alert description      |
| confidence | float  | No       | 0.87             | Model confidence score |
| device_key | string | Yes      | —                | Device auth key        |

**Response:**
```json
{
  "success": true,
  "alert_id": "alert_abc123"
}
```

**What it does:**
1. Creates a **critical severity** fire alert
2. **Broadcasts notification to ALL users**: "Fire Alert! Fire detected at [parking]. Please evacuate immediately."
3. Sends real-time WebSocket update to admin channel

---

### `POST /api/v1/iot/theft-alert`

Report a weapon/theft detection event from the AI model.

**Auth:** device_key query parameter

**Query Parameters:**
| Parameter   | Type   | Required | Default                       | Description                    |
|-------------|--------|----------|-------------------------------|--------------------------------|
| parking_id  | string | Yes      | —                             | Parking location               |
| message     | string | No       | "Suspicious activity detected"| Alert description              |
| confidence  | float  | No       | 0.80                          | Model confidence score         |
| weapon_type | string | No       | "unknown"                     | Detected type: gun, knife, unknown |
| device_key  | string | Yes      | —                             | Device auth key                |

**Response:**
```json
{
  "success": true,
  "alert_id": "alert_abc123"
}
```

**What it does:**
1. Creates a **high severity** theft alert with weapon type info
2. **Broadcasts "Security Alert!" notification to ALL users**
3. Sends real-time WebSocket update to admin channel with weapon type and confidence

---

### `POST /api/v1/iot/slot-update`

Report slot occupancy change from ESP32 sensors.

**Auth:** device_key query parameter

**Query Parameters:**
| Parameter   | Type   | Required | Description                |
|-------------|--------|----------|----------------------------|
| parking_id  | string | Yes      | Parking location           |
| slot_number | string | Yes      | Slot identifier (e.g. "A05") |
| status      | string | Yes      | "available" or "occupied"  |
| device_key  | string | Yes      | Device auth key            |

**Response:**
```json
{
  "success": true,
  "slot_id": "parking_1_slot_A05",
  "status": "available"
}
```

**What it does:**
1. Updates the slot's status in the database
2. Adjusts parking available/occupied slot counts
3. **If slot became available:** notifies all spot watchers for this parking and auto-unsubscribes them
4. Broadcasts real-time update to parking-specific and admin WebSocket channels

---

### `POST /api/v1/iot/gate-control`

Send a gate command to ESP32 via WebSocket.

**Auth:** device_key query parameter

**Query Parameters:**
| Parameter  | Type   | Required | Default  | Description           |
|------------|--------|----------|----------|-----------------------|
| parking_id | string | Yes      | —        | Parking location      |
| gate_type  | string | No       | "entry"  | "entry" or "exit"     |
| action     | string | No       | "open"   | "open" or "close"     |
| device_key | string | Yes      | —        | Device auth key       |

**What it does:** Sends a `gate_command` message to the ESP32 connected via WebSocket on the `gate:{parking_id}` channel.

---

## 21. WebSocket Endpoints

### `WS /ws/parking/{parking_id}`

Real-time updates for a specific parking.

**Auth:** None (public)

**Events received:**
- `slot_update` — when a slot status changes
- `connected` — initial connection confirmation

**Usage:** Mobile app connects to this to show live slot availability.

---

### `WS /ws/admin`

Real-time feed for admin dashboard.

**Auth:** None (open for dashboard)

**Events received:**
- `plate_detected` — ALPR detection with verification result
- `slot_update` — slot status change
- `gate_update` — gate opened/closed
- `fire_alert` — fire detected
- `theft_alert` — weapon/suspicious activity detected
- `connected` — initial connection confirmation

---

### `WS /ws/gate/{parking_id}`

Two-way communication with ESP32 gate controllers.

**Auth:** `device_key` query parameter

**Events sent to ESP32:**
- `gate_command` — `{"type": "gate_command", "gate_type": "entry|exit", "action": "open|close"}`

**Events received from ESP32:**
- `ping` — health check (responds with `pong`)
- `gate_status` — gate opened/closed status
- `slot_update` — sensor reports slot change
- `plate_detected` — ALPR detection (triggers booking verification)
- `fire_alert` — fire detection model trigger
- `theft_alert` — weapon detection model trigger

---

## 22. Data Models Reference

### Enums

| Enum | Values |
|------|--------|
| SlotStatus | `available`, `occupied`, `reserved` |
| BookingStatus | `pending`, `confirmed`, `active`, `completed`, `cancelled` |
| PaymentStatus | `pending`, `completed`, `failed`, `refunded` |
| NotificationType | `booking`, `payment`, `promo`, `security`, `system`, `alert` |
| AlertType | `fire`, `theft`, `system`, `gate`, `security` |
| AlertStatus | `active`, `acknowledged`, `resolved` |
| GenderEnum | `male`, `female`, `other` |

### Booking Status Flow

```
[User creates booking]
        │
        ▼
    CONFIRMED ──────────────────► CANCELLED (user cancels)
        │                              │
        │ (car arrives / QR scan       │ refund issued
        │  / ALPR plate match)         │ slot freed
        ▼
      ACTIVE
        │
        │ (car exits / QR scan
        │  / ALPR plate match)
        ▼
    COMPLETED
        │
        │ overstay charges
        │ calculated, slot freed
        ▼
      [done]
```

### Alert Lifecycle

```
    ACTIVE ──► ACKNOWLEDGED ──► RESOLVED
      │              │              │
   (created)    (admin saw it)  (admin fixed it,
                                 resolved_at and
                                 resolved_by recorded)
```

### ALPR Verification Flow

```
Camera detects plate
        │
        ▼
POST /iot/plate-detect
        │
        ├── action=entry
        │       │
        │       ├── Booking found (confirmed) ──► Check-in + Gate OPEN
        │       │
        │       └── No booking ──► Security alert + Gate CLOSED
        │
        └── action=exit
                │
                ├── Booking found (active) ──► Check-out + Gate OPEN + Notify watchers
                │
                └── No booking ──► Gate OPEN (don't trap car) + Admin alert
```

### Price Calculation

```
base_amount = hours * parking.rate_per_hour
fees = base_amount * 0.05 (5%)
total = base_amount + fees

On check-out (if overstayed):
  extra_hours = actual_duration - booked_duration
  extra_amount = extra_hours * rate_per_hour
  extra_fees = extra_amount * 0.05
  total += extra_amount + extra_fees
```
