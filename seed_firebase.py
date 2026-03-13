"""
Seed Firebase Firestore with demo data for Parkify.
Run: python seed_firebase.py
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth as fb_auth
from datetime import datetime, timedelta
import random
import uuid

# ─── Init Firebase ─────────────────────────────────
# Place your Firebase Admin SDK JSON file as "serviceAccountKey.json" in the project root
import os
cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
if not os.path.exists(cred_path):
    print(f"[ERROR] Firebase credentials not found at: {cred_path}")
    print("   Download your serviceAccountKey.json from Firebase Console")
    print("   and place it in the project root directory.")
    exit(1)
cred = credentials.Certificate(cred_path)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

now = datetime.utcnow()
print("Seeding Parkify Firebase...")
print(f"Project: {app.project_id}\n")


# ─── 1. Users ──────────────────────────────────────
print("[1/8] Creating users...")

users_data = {
    "admin_user": {
        "email": "admin@parkify.com",
        "name": "Admin Parkify",
        "first_name": "Admin",
        "last_name": "Parkify",
        "role": "admin",
        "phone": "+20 1000000000",
        "gender": "male",
        "address": "Cairo, Egypt",
        "profile_photo": None,
        "is_active": True,
        "cars": [],
        "payment_methods": [],
        "favorites": ["parking_1", "parking_4"],
        "created_at": (now - timedelta(days=180)).isoformat()
    },
    "user_amira": {
        "email": "amira@gmail.com",
        "name": "Amira Elmohndes",
        "first_name": "Amira",
        "last_name": "Elmohndes",
        "role": "user",
        "phone": "+20 0967 834 888",
        "gender": "female",
        "address": "New Cairo, Egypt",
        "profile_photo": None,
        "is_active": True,
        "cars": [
            {"id": "car_1", "license_plate": "\u0623 \u0628 \u062c 1234", "make": "Toyota", "model": "Corolla", "color": "White", "is_default": True},
            {"id": "car_2", "license_plate": "\u0645 \u0646 \u0648 5678", "make": "Hyundai", "model": "Elantra", "color": "Silver", "is_default": False}
        ],
        "payment_methods": [
            {"id": "pm_1", "method_type": "card", "last_four": "4242", "card_holder": "Amira Elmohndes", "expiry": "12/26", "is_default": True},
            {"id": "pm_2", "method_type": "card", "last_four": "8888", "card_holder": "Amira Elmohndes", "expiry": "03/27", "is_default": False}
        ],
        "favorites": ["parking_1", "parking_2"],
        "created_at": (now - timedelta(days=90)).isoformat()
    },
    "user_ahmed": {
        "email": "ahmed@gmail.com",
        "name": "Ahmed Hassan",
        "first_name": "Ahmed",
        "last_name": "Hassan",
        "role": "user",
        "phone": "+20 1122334455",
        "gender": "male",
        "address": "Maadi, Cairo",
        "profile_photo": None,
        "is_active": True,
        "cars": [
            {"id": "car_3", "license_plate": "\u0633 \u0639 \u062f 9012", "make": "BMW", "model": "X5", "color": "Black", "is_default": True}
        ],
        "payment_methods": [
            {"id": "pm_3", "method_type": "card", "last_four": "1111", "card_holder": "Ahmed Hassan", "expiry": "08/27", "is_default": True}
        ],
        "favorites": ["parking_4"],
        "created_at": (now - timedelta(days=60)).isoformat()
    },
    "user_sara": {
        "email": "sara@gmail.com",
        "name": "Sara Ali",
        "first_name": "Sara",
        "last_name": "Ali",
        "role": "user",
        "phone": "+20 1098765432",
        "gender": "female",
        "address": "Heliopolis, Cairo",
        "profile_photo": None,
        "is_active": True,
        "cars": [
            {"id": "car_4", "license_plate": "\u0643 \u0644 \u0645 3456", "make": "Mercedes", "model": "C200", "color": "White", "is_default": True}
        ],
        "payment_methods": [
            {"id": "pm_4", "method_type": "apple_pay", "last_four": None, "card_holder": "Sara Ali", "expiry": None, "is_default": True}
        ],
        "favorites": ["parking_1", "parking_3", "parking_5"],
        "created_at": (now - timedelta(days=30)).isoformat()
    },
    "user_omar": {
        "email": "omar@gmail.com",
        "name": "Omar Khaled",
        "first_name": "Omar",
        "last_name": "Khaled",
        "role": "user",
        "phone": "+20 1234567890",
        "gender": "male",
        "address": "6th of October, Giza",
        "profile_photo": None,
        "is_active": True,
        "cars": [
            {"id": "car_5", "license_plate": "\u0641 \u0642 \u0631 7890", "make": "Kia", "model": "Sportage", "color": "Red", "is_default": True},
            {"id": "car_6", "license_plate": "\u062a \u062b \u062e 2345", "make": "Nissan", "model": "Sunny", "color": "Gray", "is_default": False}
        ],
        "payment_methods": [],
        "favorites": [],
        "created_at": (now - timedelta(days=15)).isoformat()
    }
}

# Create Firebase Auth users too
auth_users = [
    ("admin@parkify.com", "admin123", "Admin Parkify"),
    ("amira@gmail.com", "user123", "Amira Elmohndes"),
    ("ahmed@gmail.com", "user123", "Ahmed Hassan"),
    ("sara@gmail.com", "user123", "Sara Ali"),
    ("omar@gmail.com", "user123", "Omar Khaled"),
]

for email, password, display_name in auth_users:
    try:
        fb_auth.get_user_by_email(email)
        print(f"  Auth user exists: {email}")
    except fb_auth.UserNotFoundError:
        fb_auth.create_user(email=email, password=password, display_name=display_name)
        print(f"  Auth user created: {email}")

for uid, data in users_data.items():
    db.collection("users").document(uid).set(data)
print(f"  {len(users_data)} users written to Firestore")


# ─── 2. Parkings ──────────────────────────────────
print("[2/8] Creating parkings...")

parkings_data = {
    "parking_1": {
        "name": "Cairo Festival City Mall",
        "description": "Premium covered parking with 24/7 security and EV charging stations",
        "location": {"latitude": 30.0285, "longitude": 31.4085, "address": "New Cairo, Cairo Governorate", "city": "Cairo", "country": "Egypt"},
        "parking_type": "covered",
        "total_slots": 50, "available_slots": 35, "occupied_slots": 15,
        "rate_per_hour": 20.0, "currency": "EGP",
        "amenities": ["covered", "cctv", "ev_charger", "24_7", "security"],
        "images": [], "rating": 4.5, "review_count": 128,
        "is_24_7": True, "is_active": True
    },
    "parking_2": {
        "name": "Central Plaza Parking",
        "description": "Convenient downtown parking near Tahrir Square",
        "location": {"latitude": 30.0444, "longitude": 31.2357, "address": "Downtown Cairo", "city": "Cairo", "country": "Egypt"},
        "parking_type": "multi_level",
        "total_slots": 80, "available_slots": 42, "occupied_slots": 38,
        "rate_per_hour": 15.0, "currency": "EGP",
        "amenities": ["covered", "cctv", "24_7"],
        "images": [], "rating": 4.2, "review_count": 89,
        "is_24_7": True, "is_active": True
    },
    "parking_3": {
        "name": "North Beach Parking",
        "description": "Open air beach parking along the Corniche",
        "location": {"latitude": 31.2001, "longitude": 29.9187, "address": "Corniche Road, Alexandria", "city": "Alexandria", "country": "Egypt"},
        "parking_type": "uncovered",
        "total_slots": 100, "available_slots": 78, "occupied_slots": 22,
        "rate_per_hour": 10.0, "currency": "EGP",
        "amenities": ["cctv", "24_7"],
        "images": [], "rating": 3.8, "review_count": 45,
        "is_24_7": True, "is_active": True
    },
    "parking_4": {
        "name": "Maadi Grand Mall",
        "description": "Underground parking with valet service and premium security",
        "location": {"latitude": 29.9602, "longitude": 31.2569, "address": "Maadi, Cairo", "city": "Cairo", "country": "Egypt"},
        "parking_type": "covered",
        "total_slots": 120, "available_slots": 65, "occupied_slots": 55,
        "rate_per_hour": 25.0, "currency": "EGP",
        "amenities": ["covered", "cctv", "ev_charger", "24_7", "security", "valet"],
        "images": [], "rating": 4.7, "review_count": 203,
        "is_24_7": True, "is_active": True
    },
    "parking_5": {
        "name": "Heliopolis Square Parking",
        "description": "Open-air parking near Heliopolis square and metro station",
        "location": {"latitude": 30.0866, "longitude": 31.3417, "address": "Heliopolis, Cairo", "city": "Cairo", "country": "Egypt"},
        "parking_type": "uncovered",
        "total_slots": 60, "available_slots": 12, "occupied_slots": 48,
        "rate_per_hour": 12.0, "currency": "EGP",
        "amenities": ["cctv", "security"],
        "images": [], "rating": 3.5, "review_count": 34,
        "is_24_7": False, "is_active": True
    },
    "parking_6": {
        "name": "Smart Village Parking",
        "description": "Tech park covered parking with automated gates",
        "location": {"latitude": 30.0709, "longitude": 31.0175, "address": "Smart Village, 6th of October", "city": "Giza", "country": "Egypt"},
        "parking_type": "covered",
        "total_slots": 200, "available_slots": 140, "occupied_slots": 60,
        "rate_per_hour": 15.0, "currency": "EGP",
        "amenities": ["covered", "cctv", "ev_charger", "24_7", "security"],
        "images": [], "rating": 4.3, "review_count": 67,
        "is_24_7": True, "is_active": True
    },
    "parking_7": {
        "name": "City Stars Mall Parking",
        "description": "Large multi-level parking at City Stars shopping mall",
        "location": {"latitude": 30.0734, "longitude": 31.3454, "address": "Nasr City, Cairo", "city": "Cairo", "country": "Egypt"},
        "parking_type": "multi_level",
        "total_slots": 300, "available_slots": 180, "occupied_slots": 120,
        "rate_per_hour": 18.0, "currency": "EGP",
        "amenities": ["covered", "cctv", "ev_charger", "24_7", "security", "valet"],
        "images": [], "rating": 4.6, "review_count": 312,
        "is_24_7": True, "is_active": True
    }
}

for pid, data in parkings_data.items():
    db.collection("parkings").document(pid).set(data)
print(f"  {len(parkings_data)} parkings written")


# ─── 3. Parking Slots ────────────────────────────
print("[3/8] Creating parking slots...")

slot_count = 0
for parking_id, parking in parkings_data.items():
    batch = db.batch()
    count = 0
    for i in range(parking["total_slots"]):
        floor = (i // 20) + 1
        section = chr(65 + (i // 10) % 3)
        slot_num = (i % 10) + 1
        slot_number = f"{section}{slot_num:02d}"
        slot_id = f"{parking_id}_slot_{slot_number}"

        slot_data = {
            "parking_id": parking_id,
            "slot_number": slot_number,
            "floor": floor,
            "section": section,
            "status": "available" if i >= parking["occupied_slots"] else "occupied",
            "is_handicap": i % 10 == 0,
            "is_ev_charging": i % 15 == 0,
            "current_vehicle_plate": None
        }
        batch.set(db.collection("parking_slots").document(slot_id), slot_data)
        count += 1
        slot_count += 1

        # Firestore batch limit is 500
        if count >= 450:
            batch.commit()
            batch = db.batch()
            count = 0

    if count > 0:
        batch.commit()

print(f"  {slot_count} slots written")


# ─── 4. Bookings ─────────────────────────────────
print("[4/8] Creating bookings...")

bookings_data = [
    {
        "id": "booking_001",
        "user_id": "user_amira",
        "parking_id": "parking_1",
        "parking_name": "Cairo Festival City Mall",
        "parking_address": "New Cairo, Cairo Governorate",
        "slot_id": "parking_1_slot_A05",
        "slot_number": "A05",
        "floor": 1, "section": "A",
        "vehicle_plate": "\u0623 \u0628 \u062c 1234",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
        "actual_exit_time": None,
        "status": "active",
        "total_hours": 3.0,
        "amount": 60.0, "fees": 3.0, "total_amount": 63.0,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "card",
        "created_at": (now - timedelta(hours=1, minutes=15)).isoformat()
    },
    {
        "id": "booking_002",
        "user_id": "user_ahmed",
        "parking_id": "parking_4",
        "parking_name": "Maadi Grand Mall",
        "parking_address": "Maadi, Cairo",
        "slot_id": "parking_4_slot_B03",
        "slot_number": "B03",
        "floor": 1, "section": "B",
        "vehicle_plate": "\u0633 \u0639 \u062f 9012",
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "actual_exit_time": None,
        "status": "active",
        "total_hours": 3.0,
        "amount": 75.0, "fees": 3.75, "total_amount": 78.75,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "card",
        "created_at": (now - timedelta(hours=2, minutes=10)).isoformat()
    },
    {
        "id": "booking_003",
        "user_id": "user_sara",
        "parking_id": "parking_1",
        "parking_name": "Cairo Festival City Mall",
        "parking_address": "New Cairo, Cairo Governorate",
        "slot_id": "parking_1_slot_B01",
        "slot_number": "B01",
        "floor": 1, "section": "B",
        "vehicle_plate": "\u0643 \u0644 \u0645 3456",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=4)).isoformat(),
        "actual_exit_time": None,
        "status": "confirmed",
        "total_hours": 3.0,
        "amount": 60.0, "fees": 3.0, "total_amount": 63.0,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "apple_pay",
        "created_at": (now - timedelta(minutes=30)).isoformat()
    },
    {
        "id": "booking_004",
        "user_id": "user_amira",
        "parking_id": "parking_2",
        "parking_name": "Central Plaza Parking",
        "parking_address": "Downtown Cairo",
        "slot_id": "parking_2_slot_A02",
        "slot_number": "A02",
        "floor": 1, "section": "A",
        "vehicle_plate": "\u0645 \u0646 \u0648 5678",
        "start_time": (now - timedelta(days=2, hours=3)).isoformat(),
        "end_time": (now - timedelta(days=2, hours=1)).isoformat(),
        "actual_exit_time": (now - timedelta(days=2, hours=1, minutes=10)).isoformat(),
        "status": "completed",
        "total_hours": 2.0,
        "amount": 30.0, "fees": 1.5, "total_amount": 31.5,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "card",
        "created_at": (now - timedelta(days=2, hours=3, minutes=20)).isoformat()
    },
    {
        "id": "booking_005",
        "user_id": "user_ahmed",
        "parking_id": "parking_1",
        "parking_name": "Cairo Festival City Mall",
        "parking_address": "New Cairo, Cairo Governorate",
        "slot_id": "parking_1_slot_C08",
        "slot_number": "C08",
        "floor": 2, "section": "C",
        "vehicle_plate": "\u0633 \u0639 \u062f 9012",
        "start_time": (now - timedelta(days=5, hours=4)).isoformat(),
        "end_time": (now - timedelta(days=5, hours=2)).isoformat(),
        "actual_exit_time": (now - timedelta(days=5, hours=2)).isoformat(),
        "status": "completed",
        "total_hours": 2.0,
        "amount": 40.0, "fees": 2.0, "total_amount": 42.0,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "card",
        "created_at": (now - timedelta(days=5, hours=4, minutes=30)).isoformat()
    },
    {
        "id": "booking_006",
        "user_id": "user_omar",
        "parking_id": "parking_3",
        "parking_name": "North Beach Parking",
        "parking_address": "Corniche Road, Alexandria",
        "slot_id": "parking_3_slot_A07",
        "slot_number": "A07",
        "floor": 1, "section": "A",
        "vehicle_plate": "\u0641 \u0642 \u0631 7890",
        "start_time": (now - timedelta(days=1, hours=5)).isoformat(),
        "end_time": (now - timedelta(days=1, hours=1)).isoformat(),
        "actual_exit_time": None,
        "status": "cancelled",
        "total_hours": 4.0,
        "amount": 40.0, "fees": 2.0, "total_amount": 42.0,
        "currency": "EGP",
        "payment_status": "refunded",
        "payment_method": "card",
        "created_at": (now - timedelta(days=1, hours=6)).isoformat()
    },
    {
        "id": "booking_007",
        "user_id": "user_sara",
        "parking_id": "parking_7",
        "parking_name": "City Stars Mall Parking",
        "parking_address": "Nasr City, Cairo",
        "slot_id": "parking_7_slot_A03",
        "slot_number": "A03",
        "floor": 1, "section": "A",
        "vehicle_plate": "\u0643 \u0644 \u0645 3456",
        "start_time": (now - timedelta(days=3)).isoformat(),
        "end_time": (now - timedelta(days=3) + timedelta(hours=2)).isoformat(),
        "actual_exit_time": (now - timedelta(days=3) + timedelta(hours=2)).isoformat(),
        "status": "completed",
        "total_hours": 2.0,
        "amount": 36.0, "fees": 1.8, "total_amount": 37.8,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "apple_pay",
        "created_at": (now - timedelta(days=3, minutes=15)).isoformat()
    },
    {
        "id": "booking_008",
        "user_id": "user_omar",
        "parking_id": "parking_5",
        "parking_name": "Heliopolis Square Parking",
        "parking_address": "Heliopolis, Cairo",
        "slot_id": "parking_5_slot_B02",
        "slot_number": "B02",
        "floor": 1, "section": "B",
        "vehicle_plate": "\u062a \u062b \u062e 2345",
        "start_time": (now - timedelta(hours=3)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "actual_exit_time": None,
        "status": "active",
        "total_hours": 4.0,
        "amount": 48.0, "fees": 2.4, "total_amount": 50.4,
        "currency": "EGP",
        "payment_status": "completed",
        "payment_method": "card",
        "created_at": (now - timedelta(hours=3, minutes=20)).isoformat()
    }
]

for b in bookings_data:
    db.collection("bookings").document(b["id"]).set(b)
print(f"  {len(bookings_data)} bookings written")


# ─── 5. Notifications ────────────────────────────
print("[5/8] Creating notifications...")

notifications_data = [
    {"id": "notif_001", "user_id": "user_amira", "title": "Booking Successful!", "message": "You have successfully booked slot A05 at Cairo Festival City Mall for 3 hours.", "notification_type": "booking", "is_read": False, "data": {"booking_id": "booking_001"}, "created_at": (now - timedelta(hours=1, minutes=15)).isoformat()},
    {"id": "notif_002", "user_id": "user_amira", "title": "Payment Confirmed", "message": "Payment of 63.00 EGP was successful via card ending 4242.", "notification_type": "payment", "is_read": False, "data": {"amount": 63.0}, "created_at": (now - timedelta(hours=1, minutes=14)).isoformat()},
    {"id": "notif_003", "user_id": "user_amira", "title": "30% Off Your Next Park", "message": "Use code PARK30 to get 30% discount on your next booking!", "notification_type": "promo", "is_read": True, "data": {"promo_code": "PARK30"}, "created_at": (now - timedelta(days=1)).isoformat()},
    {"id": "notif_004", "user_id": "user_amira", "title": "Account Security", "message": "We've updated our privacy policy and terms of service. Please review the changes.", "notification_type": "security", "is_read": True, "data": None, "created_at": (now - timedelta(days=1, hours=3)).isoformat()},
    {"id": "notif_005", "user_id": "user_amira", "title": "Previous Booking Completed", "message": "Your parking session at Central Plaza Parking has ended. Thank you!", "notification_type": "booking", "is_read": True, "data": {"booking_id": "booking_004"}, "created_at": (now - timedelta(days=2, hours=1)).isoformat()},
    {"id": "notif_006", "user_id": "user_ahmed", "title": "Booking Successful!", "message": "You have successfully booked slot B03 at Maadi Grand Mall for 3 hours.", "notification_type": "booking", "is_read": False, "data": {"booking_id": "booking_002"}, "created_at": (now - timedelta(hours=2, minutes=10)).isoformat()},
    {"id": "notif_007", "user_id": "user_ahmed", "title": "Payment Confirmed", "message": "Payment of 78.75 EGP was successful via card ending 1111.", "notification_type": "payment", "is_read": False, "data": {"amount": 78.75}, "created_at": (now - timedelta(hours=2, minutes=9)).isoformat()},
    {"id": "notif_008", "user_id": "user_ahmed", "title": "Welcome to Parkify!", "message": "Your account has been created. Start finding parking spots near you.", "notification_type": "system", "is_read": True, "data": None, "created_at": (now - timedelta(days=60)).isoformat()},
    {"id": "notif_009", "user_id": "user_sara", "title": "Booking Confirmed", "message": "Your booking at Cairo Festival City Mall is confirmed for today.", "notification_type": "booking", "is_read": False, "data": {"booking_id": "booking_003"}, "created_at": (now - timedelta(minutes=30)).isoformat()},
    {"id": "notif_010", "user_id": "user_sara", "title": "Rate Your Experience", "message": "How was your parking at City Stars Mall? Leave a review!", "notification_type": "system", "is_read": False, "data": {"parking_id": "parking_7"}, "created_at": (now - timedelta(days=2)).isoformat()},
    {"id": "notif_011", "user_id": "user_omar", "title": "Booking Cancelled", "message": "Your booking at North Beach Parking has been cancelled. Refund of 42.00 EGP is being processed.", "notification_type": "booking", "is_read": True, "data": {"booking_id": "booking_006"}, "created_at": (now - timedelta(days=1, hours=5)).isoformat()},
    {"id": "notif_012", "user_id": "user_omar", "title": "Booking Successful!", "message": "You have successfully booked slot B02 at Heliopolis Square Parking for 4 hours.", "notification_type": "booking", "is_read": False, "data": {"booking_id": "booking_008"}, "created_at": (now - timedelta(hours=3, minutes=20)).isoformat()},
    {"id": "notif_013", "user_id": "user_amira", "title": "Parking Reminder", "message": "Your parking at Cairo Festival City Mall expires in 2 hours.", "notification_type": "booking", "is_read": False, "data": {"booking_id": "booking_001"}, "created_at": (now - timedelta(minutes=5)).isoformat()},
    {"id": "notif_014", "user_id": "user_sara", "title": "New Parking Added", "message": "Smart Village Parking is now available! Check it out.", "notification_type": "promo", "is_read": True, "data": {"parking_id": "parking_6"}, "created_at": (now - timedelta(days=7)).isoformat()},
]

for n in notifications_data:
    db.collection("notifications").document(n["id"]).set(n)
print(f"  {len(notifications_data)} notifications written")


# ─── 6. Alerts ───────────────────────────────────
print("[6/8] Creating alerts...")

alerts_data = [
    {"id": "alert_001", "parking_id": "parking_1", "parking_name": "Cairo Festival City Mall", "alert_type": "fire", "severity": "critical", "message": "Smoke detected in Section B, Floor 2. Fire detection model confidence: 87%.", "status": "active", "created_at": (now - timedelta(minutes=5)).isoformat(), "resolved_at": None, "resolved_by": None},
    {"id": "alert_002", "parking_id": "parking_2", "parking_name": "Central Plaza Parking", "alert_type": "theft", "severity": "high", "message": "Suspicious activity detected near Gate B. Weapon detection model triggered with 94.8% confidence.", "status": "active", "created_at": (now - timedelta(minutes=15)).isoformat(), "resolved_at": None, "resolved_by": None},
    {"id": "alert_003", "parking_id": "parking_3", "parking_name": "North Beach Parking", "alert_type": "gate", "severity": "medium", "message": "Entry gate malfunction detected. Gate not responding to open commands.", "status": "resolved", "created_at": (now - timedelta(hours=2)).isoformat(), "resolved_at": (now - timedelta(hours=1)).isoformat(), "resolved_by": "admin_user"},
    {"id": "alert_004", "parking_id": "parking_4", "parking_name": "Maadi Grand Mall", "alert_type": "system", "severity": "low", "message": "Slot sensor B07 intermittent connection. May need maintenance.", "status": "acknowledged", "created_at": (now - timedelta(hours=6)).isoformat(), "resolved_at": None, "resolved_by": None},
    {"id": "alert_005", "parking_id": "parking_7", "parking_name": "City Stars Mall Parking", "alert_type": "fire", "severity": "critical", "message": "Heat anomaly detected in underground level 2. Confidence: 72%.", "status": "resolved", "created_at": (now - timedelta(days=1)).isoformat(), "resolved_at": (now - timedelta(hours=22)).isoformat(), "resolved_by": "admin_user"},
]

for a in alerts_data:
    db.collection("alerts").document(a["id"]).set(a)
print(f"  {len(alerts_data)} alerts written")


# ─── 7. Vehicle Logs ─────────────────────────────
print("[7/8] Creating vehicle logs...")

plates = [
    "\u0623 \u0628 \u062c 1234", "\u0645 \u0646 \u0648 5678", "\u0633 \u0639 \u062f 9012",
    "\u0643 \u0644 \u0645 3456", "\u0641 \u0642 \u0631 7890", "\u062a \u062b \u062e 2345",
    "\u0630 \u0632 \u0634 6789", "\u0635 \u0636 \u0637 0123",
    "\u0639 \u063a \u0638 4567", "\u062d \u062e \u062f 8901"
]

vehicle_logs = []
for i in range(30):
    parking_idx = (i % 7) + 1
    parking_id = f"parking_{parking_idx}"
    pname = parkings_data[parking_id]["name"]
    log = {
        "id": f"vlog_{i+1:03d}",
        "parking_id": parking_id,
        "parking_name": pname,
        "vehicle_plate": plates[i % len(plates)],
        "action": "entry" if i % 2 == 0 else "exit",
        "gate": "Gate A" if i % 3 != 2 else "Gate B",
        "timestamp": (now - timedelta(hours=i * 0.7, minutes=random.randint(0, 30))).isoformat(),
        "plate_image": None,
        "confidence": round(random.uniform(0.88, 0.99), 3)
    }
    vehicle_logs.append(log)

batch = db.batch()
for log in vehicle_logs:
    batch.set(db.collection("vehicle_logs").document(log["id"]), log)
batch.commit()
print(f"  {len(vehicle_logs)} vehicle logs written")


# ─── 8. Support Tickets ─────────────────────────
print("[8/8] Creating support tickets...")

tickets_data = [
    {"id": "ticket_001", "user_id": "user_amira", "subject": "Gate not opening", "message": "The entry gate at Cairo Festival City did not open with my QR code. I had to wait 5 minutes for manual override.", "category": "technical", "status": "open", "created_at": (now - timedelta(hours=4)).isoformat(), "updated_at": None},
    {"id": "ticket_002", "user_id": "user_ahmed", "subject": "Wrong charge amount", "message": "I was charged 78.75 EGP but my booking was only 2 hours at 25 EGP/hr. Please check.", "category": "payment", "status": "in_progress", "created_at": (now - timedelta(days=1)).isoformat(), "updated_at": (now - timedelta(hours=12)).isoformat()},
    {"id": "ticket_003", "user_id": "user_omar", "subject": "Refund not received", "message": "I cancelled booking_006 yesterday but haven't received my refund of 42.00 EGP.", "category": "payment", "status": "open", "created_at": (now - timedelta(hours=8)).isoformat(), "updated_at": None},
    {"id": "ticket_004", "user_id": "user_sara", "subject": "App shows wrong slot", "message": "The app showed slot A03 at City Stars as available but when I got there it was occupied.", "category": "booking", "status": "resolved", "created_at": (now - timedelta(days=3)).isoformat(), "updated_at": (now - timedelta(days=2)).isoformat()},
]

for t in tickets_data:
    db.collection("support_tickets").document(t["id"]).set(t)
print(f"  {len(tickets_data)} tickets written")


# ─── Done ────────────────────────────────────────
firebase_admin.delete_app(app)

print("\n" + "=" * 50)
print("  Firebase seeding complete!")
print("=" * 50)
print(f"""
  Collections created:
    - users:            {len(users_data)} documents
    - parkings:         {len(parkings_data)} documents
    - parking_slots:    {slot_count} documents
    - bookings:         {len(bookings_data)} documents
    - notifications:    {len(notifications_data)} documents
    - alerts:           {len(alerts_data)} documents
    - vehicle_logs:     {len(vehicle_logs)} documents
    - support_tickets:  {len(tickets_data)} documents

  Firebase Auth users:  {len(auth_users)} accounts
    - admin@parkify.com  / admin123
    - amira@gmail.com    / user123
    - ahmed@gmail.com    / user123
    - sara@gmail.com     / user123
    - omar@gmail.com     / user123

  Total documents:      {len(users_data) + len(parkings_data) + slot_count + len(bookings_data) + len(notifications_data) + len(alerts_data) + len(vehicle_logs) + len(tickets_data)}
""")
