"""Services with Demo Data"""

from typing import List, Optional
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
import uuid
import random
import json
import hashlib

from passlib.context import CryptContext
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ADMIN_HASH = _pwd_ctx.hash("admin123")
_USER_HASH = _pwd_ctx.hash("user123")


class ParkingService:
    def __init__(self):
        # Demo parkings
        self._demo_parkings = {
            "parking_1": {
                "id": "parking_1",
                "name": "Cairo Festival City Mall",
                "description": "Premium covered parking with 24/7 security",
                "location": {
                    "latitude": 30.0285,
                    "longitude": 31.4085,
                    "address": "New Cairo, Cairo Governorate",
                    "city": "Cairo",
                    "country": "Egypt"
                },
                "parking_type": "covered",
                "total_slots": 50,
                "available_slots": 35,
                "occupied_slots": 15,
                "rate_per_hour": 20.0,
                "currency": "EGP",
                "amenities": ["covered", "cctv", "ev_charger", "24_7", "security"],
                "images": [],
                "rating": 4.5,
                "review_count": 128,
                "is_24_7": True,
                "is_active": True
            },
            "parking_2": {
                "id": "parking_2",
                "name": "Central Plaza Parking",
                "description": "Convenient downtown parking",
                "location": {
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "address": "Downtown Cairo",
                    "city": "Cairo",
                    "country": "Egypt"
                },
                "parking_type": "multi_level",
                "total_slots": 80,
                "available_slots": 42,
                "occupied_slots": 38,
                "rate_per_hour": 15.0,
                "currency": "EGP",
                "amenities": ["covered", "cctv", "24_7"],
                "images": [],
                "rating": 4.2,
                "review_count": 89,
                "is_24_7": True,
                "is_active": True
            },
            "parking_3": {
                "id": "parking_3",
                "name": "North Beach Parking",
                "description": "Open air beach parking",
                "location": {
                    "latitude": 31.2001,
                    "longitude": 29.9187,
                    "address": "Corniche Road, Alexandria",
                    "city": "Alexandria",
                    "country": "Egypt"
                },
                "parking_type": "uncovered",
                "total_slots": 100,
                "available_slots": 78,
                "occupied_slots": 22,
                "rate_per_hour": 10.0,
                "currency": "EGP",
                "amenities": ["cctv", "24_7"],
                "images": [],
                "rating": 3.8,
                "review_count": 45,
                "is_24_7": True,
                "is_active": True
            },
            "parking_4": {
                "id": "parking_4",
                "name": "Maadi Grand Mall",
                "description": "Underground parking with valet service",
                "location": {
                    "latitude": 29.9602,
                    "longitude": 31.2569,
                    "address": "Maadi, Cairo",
                    "city": "Cairo",
                    "country": "Egypt"
                },
                "parking_type": "covered",
                "total_slots": 120,
                "available_slots": 65,
                "occupied_slots": 55,
                "rate_per_hour": 25.0,
                "currency": "EGP",
                "amenities": ["covered", "cctv", "ev_charger", "24_7", "security", "valet"],
                "images": [],
                "rating": 4.7,
                "review_count": 203,
                "is_24_7": True,
                "is_active": True
            },
            "parking_5": {
                "id": "parking_5",
                "name": "Heliopolis Square Parking",
                "description": "Open-air parking near Heliopolis square",
                "location": {
                    "latitude": 30.0866,
                    "longitude": 31.3417,
                    "address": "Heliopolis, Cairo",
                    "city": "Cairo",
                    "country": "Egypt"
                },
                "parking_type": "uncovered",
                "total_slots": 60,
                "available_slots": 12,
                "occupied_slots": 48,
                "rate_per_hour": 12.0,
                "currency": "EGP",
                "amenities": ["cctv", "security"],
                "images": [],
                "rating": 3.5,
                "review_count": 34,
                "is_24_7": False,
                "is_active": True
            },
            "parking_6": {
                "id": "parking_6",
                "name": "Smart Village Parking",
                "description": "Tech park covered parking with automated gates",
                "location": {
                    "latitude": 30.0709,
                    "longitude": 31.0175,
                    "address": "Smart Village, 6th of October",
                    "city": "Giza",
                    "country": "Egypt"
                },
                "parking_type": "covered",
                "total_slots": 200,
                "available_slots": 140,
                "occupied_slots": 60,
                "rate_per_hour": 15.0,
                "currency": "EGP",
                "amenities": ["covered", "cctv", "ev_charger", "24_7", "security"],
                "images": [],
                "rating": 4.3,
                "review_count": 67,
                "is_24_7": True,
                "is_active": True
            },
            "parking_7": {
                "id": "parking_7",
                "name": "City Stars Mall Parking",
                "description": "Large multi-level parking at City Stars shopping mall",
                "location": {
                    "latitude": 30.0734,
                    "longitude": 31.3454,
                    "address": "Nasr City, Cairo",
                    "city": "Cairo",
                    "country": "Egypt"
                },
                "parking_type": "multi_level",
                "total_slots": 300,
                "available_slots": 180,
                "occupied_slots": 120,
                "rate_per_hour": 18.0,
                "currency": "EGP",
                "amenities": ["covered", "cctv", "ev_charger", "24_7", "security", "valet"],
                "images": [],
                "rating": 4.6,
                "review_count": 312,
                "is_24_7": True,
                "is_active": True
            }
        }

        # Generate slots
        self._demo_slots = {}
        for parking_id, parking in self._demo_parkings.items():
            for i in range(parking["total_slots"]):
                floor = (i // 20) + 1
                section = chr(65 + (i // 10) % 3)
                slot_num = (i % 10) + 1
                slot_number = f"{section}{slot_num:02d}"
                slot_id = f"{parking_id}_slot_{slot_number}"

                self._demo_slots[slot_id] = {
                    "id": slot_id,
                    "parking_id": parking_id,
                    "slot_number": slot_number,
                    "floor": floor,
                    "section": section,
                    "status": "available" if i >= parking["occupied_slots"] else "occupied",
                    "is_handicap": i % 10 == 0,
                    "is_ev_charging": i % 15 == 0,
                    "current_vehicle_plate": None
                }

        self._demo_bookings = {}

        # Demo users (password: admin123 and user123)
        self._demo_users = {
            "admin_user": {
                "id": "admin_user",
                "email": "admin@parkify.com",
                "name": "Admin Parkify",
                "first_name": "Admin",
                "last_name": "Parkify",
                "role": "admin",
                "password_hash": _ADMIN_HASH,
                "is_active": True,
                "phone": "+20 1000000000",
                "gender": "male",
                "address": "Cairo, Egypt",
                "profile_photo": None,
                "cars": [],
                "payment_methods": [],
                "favorites": ["parking_1", "parking_4"],
                "created_at": "2024-01-01T00:00:00"
            },
            "user_amira": {
                "id": "user_amira",
                "email": "amira@gmail.com",
                "name": "Amira Elmohndes",
                "first_name": "Amira",
                "last_name": "Elmohndes",
                "role": "user",
                "password_hash": _USER_HASH,
                "is_active": True,
                "phone": "+20 0967 834 888",
                "gender": "female",
                "address": "New Cairo, Egypt",
                "profile_photo": None,
                "cars": [
                    {"id": "car_1", "license_plate": "أ ب ج 1234", "make": "Toyota", "model": "Corolla", "color": "White", "is_default": True},
                    {"id": "car_2", "license_plate": "م ن و 5678", "make": "Hyundai", "model": "Elantra", "color": "Silver", "is_default": False}
                ],
                "payment_methods": [
                    {"id": "pm_1", "method_type": "card", "last_four": "4242", "card_holder": "Amira Elmohndes", "expiry": "12/26", "is_default": True},
                    {"id": "pm_2", "method_type": "card", "last_four": "8888", "card_holder": "Amira Elmohndes", "expiry": "03/27", "is_default": False}
                ],
                "favorites": ["parking_1", "parking_2"],
                "created_at": "2024-06-15T10:30:00"
            },
            "user_ahmed": {
                "id": "user_ahmed",
                "email": "ahmed@gmail.com",
                "name": "Ahmed Hassan",
                "first_name": "Ahmed",
                "last_name": "Hassan",
                "role": "user",
                "password_hash": _USER_HASH,
                "is_active": True,
                "phone": "+20 1122334455",
                "gender": "male",
                "address": "Maadi, Cairo",
                "profile_photo": None,
                "cars": [
                    {"id": "car_3", "license_plate": "س ع د 9012", "make": "BMW", "model": "X5", "color": "Black", "is_default": True}
                ],
                "payment_methods": [
                    {"id": "pm_3", "method_type": "card", "last_four": "1111", "card_holder": "Ahmed Hassan", "expiry": "08/27", "is_default": True}
                ],
                "favorites": ["parking_4"],
                "created_at": "2024-09-01T10:00:00"
            },
            "user_sara": {
                "id": "user_sara",
                "email": "sara@gmail.com",
                "name": "Sara Ali",
                "first_name": "Sara",
                "last_name": "Ali",
                "role": "user",
                "password_hash": _USER_HASH,
                "is_active": True,
                "phone": "+20 1098765432",
                "gender": "female",
                "address": "Heliopolis, Cairo",
                "profile_photo": None,
                "cars": [
                    {"id": "car_4", "license_plate": "ك ل م 3456", "make": "Mercedes", "model": "C200", "color": "White", "is_default": True}
                ],
                "payment_methods": [
                    {"id": "pm_4", "method_type": "apple_pay", "last_four": None, "card_holder": "Sara Ali", "expiry": None, "is_default": True}
                ],
                "favorites": ["parking_1", "parking_3", "parking_5"],
                "created_at": "2024-11-01T08:00:00"
            },
            "user_omar": {
                "id": "user_omar",
                "email": "omar@gmail.com",
                "name": "Omar Khaled",
                "first_name": "Omar",
                "last_name": "Khaled",
                "role": "user",
                "password_hash": _USER_HASH,
                "is_active": True,
                "phone": "+20 1234567890",
                "gender": "male",
                "address": "6th of October, Giza",
                "profile_photo": None,
                "cars": [
                    {"id": "car_5", "license_plate": "ف ق ر 7890", "make": "Kia", "model": "Sportage", "color": "Red", "is_default": True},
                    {"id": "car_6", "license_plate": "ت ث خ 2345", "make": "Nissan", "model": "Sunny", "color": "Gray", "is_default": False}
                ],
                "payment_methods": [],
                "favorites": [],
                "created_at": "2025-01-15T12:00:00"
            }
        }

        # Verification codes store: {email_or_phone: {"code": "123456", "expires": datetime, "verified": bool}}
        self._verification_codes = {}

        # Password reset tokens: {email_or_phone: {"code": "123456", "expires": datetime}}
        self._reset_codes = {}

        # Notifications
        self._notifications = {}
        self._init_demo_notifications()

        # Alerts
        self._alerts = {}
        self._init_demo_alerts()

        # Vehicle logs
        self._vehicle_logs = {}
        self._init_demo_vehicle_logs()

        # Support tickets
        self._support_tickets = {}

    def _init_demo_notifications(self):
        now = datetime.utcnow()
        demo_notifications = [
            {
                "id": "notif_1",
                "user_id": "user_amira",
                "title": "Booking Successful!",
                "message": "You have successfully booked a slot at Metro Parking Garage for 2 hours.",
                "notification_type": "booking",
                "is_read": False,
                "data": {"booking_id": "booking_demo1"},
                "created_at": (now - timedelta(minutes=2)).isoformat()
            },
            {
                "id": "notif_2",
                "user_id": "user_amira",
                "title": "Payment Confirmed",
                "message": "Payment of 42.00 EGP was successful via card ending 4242.",
                "notification_type": "payment",
                "is_read": False,
                "data": {"amount": 42.00},
                "created_at": (now - timedelta(hours=1)).isoformat()
            },
            {
                "id": "notif_3",
                "user_id": "user_amira",
                "title": "30% Off Your Next Park",
                "message": "Use code PARK30 to get 30% discount on your next booking!",
                "notification_type": "promo",
                "is_read": True,
                "data": {"promo_code": "PARK30"},
                "created_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "id": "notif_4",
                "user_id": "user_amira",
                "title": "Account Security",
                "message": "We've updated our privacy policy and terms of service. Please review the changes.",
                "notification_type": "security",
                "is_read": True,
                "data": None,
                "created_at": (now - timedelta(days=1, hours=3)).isoformat()
            },
            {
                "id": "notif_5",
                "user_id": "user_amira",
                "title": "Booking Reminder",
                "message": "Your parking booking at Cairo Festival City Mall starts in 30 minutes.",
                "notification_type": "booking",
                "is_read": True,
                "data": {"parking_id": "parking_1"},
                "created_at": (now - timedelta(days=2)).isoformat()
            }
        ]
        for n in demo_notifications:
            self._notifications[n["id"]] = n

    def _init_demo_alerts(self):
        now = datetime.utcnow()
        demo_alerts = [
            {
                "id": "alert_1",
                "parking_id": "parking_1",
                "parking_name": "Cairo Festival City Mall",
                "alert_type": "fire",
                "severity": "critical",
                "message": "Smoke detected in Section B, Floor 2. Fire detection model confidence: 87%.",
                "status": "active",
                "created_at": (now - timedelta(minutes=5)).isoformat(),
                "resolved_at": None,
                "resolved_by": None
            },
            {
                "id": "alert_2",
                "parking_id": "parking_2",
                "parking_name": "Central Plaza Parking",
                "alert_type": "theft",
                "severity": "high",
                "message": "Suspicious activity detected near Gate B. Weapon detection model triggered.",
                "status": "active",
                "created_at": (now - timedelta(minutes=15)).isoformat(),
                "resolved_at": None,
                "resolved_by": None
            },
            {
                "id": "alert_3",
                "parking_id": "parking_3",
                "parking_name": "North Beach Parking",
                "alert_type": "gate",
                "severity": "medium",
                "message": "Entry gate malfunction detected. Gate not responding to open commands.",
                "status": "resolved",
                "created_at": (now - timedelta(hours=2)).isoformat(),
                "resolved_at": (now - timedelta(hours=1)).isoformat(),
                "resolved_by": "admin_user"
            }
        ]
        for a in demo_alerts:
            self._alerts[a["id"]] = a

    def _init_demo_vehicle_logs(self):
        now = datetime.utcnow()
        plates = ["أ ب ج 1234", "م ن و 5678", "س ع د 9012", "ك ل م 3456", "ف ق ر 7890",
                   "ت ث خ 2345", "ذ ز ش 6789", "ص ض ط 0123"]
        demo_logs = []
        for i in range(20):
            log_id = f"vlog_{i+1}"
            parking_idx = (i % 5) + 1
            parking_id = f"parking_{parking_idx}"
            parking = self._demo_parkings[parking_id]
            demo_logs.append({
                "id": log_id,
                "parking_id": parking_id,
                "parking_name": parking["name"],
                "vehicle_plate": plates[i % len(plates)],
                "action": "entry" if i % 2 == 0 else "exit",
                "gate": "Gate A" if i % 3 == 0 else "Gate B",
                "timestamp": (now - timedelta(hours=i, minutes=random.randint(0, 59))).isoformat(),
                "plate_image": None,
                "confidence": round(random.uniform(0.85, 0.99), 2)
            })
        for log in demo_logs:
            self._vehicle_logs[log["id"]] = log

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * asin(sqrt(a))

    def get_all_parkings(self) -> List[dict]:
        return list(self._demo_parkings.values())

    def search_nearby(self, lat: float, lon: float, radius_km: float = 10, sort_by: str = "distance") -> List[dict]:
        results = []
        for parking in self._demo_parkings.values():
            if not parking["is_active"]:
                continue
            distance = self.haversine_distance(lat, lon, parking["location"]["latitude"], parking["location"]["longitude"])
            if distance <= radius_km * 1000:
                p = parking.copy()
                p["distance_meters"] = round(distance, 2)
                p["walking_time_minutes"] = round(distance / 80)
                results.append(p)

        if sort_by == "distance":
            results.sort(key=lambda x: x["distance_meters"])
        elif sort_by == "price":
            results.sort(key=lambda x: x["rate_per_hour"])
        elif sort_by == "rating":
            results.sort(key=lambda x: x["rating"], reverse=True)
        return results

    def search_by_name(self, query: str) -> List[dict]:
        query_lower = query.lower()
        results = []
        for parking in self._demo_parkings.values():
            if not parking["is_active"]:
                continue
            if (query_lower in parking["name"].lower() or
                    query_lower in parking.get("description", "").lower() or
                    query_lower in parking["location"].get("address", "").lower() or
                    query_lower in parking["location"].get("city", "").lower()):
                results.append(parking)
        return results

    def filter_parkings(self, lat: Optional[float], lon: Optional[float],
                        radius_km: float = 10, min_price: Optional[float] = None,
                        max_price: Optional[float] = None, parking_type: Optional[str] = None,
                        sort_by: str = "distance", amenities: Optional[List[str]] = None,
                        available_only: bool = True) -> List[dict]:
        results = []
        for parking in self._demo_parkings.values():
            if not parking["is_active"]:
                continue
            if available_only and parking["available_slots"] == 0:
                continue
            if min_price is not None and parking["rate_per_hour"] < min_price:
                continue
            if max_price is not None and parking["rate_per_hour"] > max_price:
                continue
            if parking_type and parking["parking_type"] != parking_type:
                continue
            if amenities:
                if not all(a in parking["amenities"] for a in amenities):
                    continue

            p = parking.copy()
            if lat is not None and lon is not None:
                distance = self.haversine_distance(lat, lon, parking["location"]["latitude"], parking["location"]["longitude"])
                if distance > radius_km * 1000:
                    continue
                p["distance_meters"] = round(distance, 2)
                p["walking_time_minutes"] = round(distance / 80)
            results.append(p)

        if sort_by == "distance" and lat is not None:
            results.sort(key=lambda x: x.get("distance_meters", 0))
        elif sort_by == "price":
            results.sort(key=lambda x: x["rate_per_hour"])
        elif sort_by == "rating":
            results.sort(key=lambda x: x["rating"], reverse=True)
        return results

    def get_parking_by_id(self, parking_id: str) -> Optional[dict]:
        return self._demo_parkings.get(parking_id)

    def get_parking_slots(self, parking_id: str, available_only: bool = False) -> List[dict]:
        slots = [s for s in self._demo_slots.values() if s["parking_id"] == parking_id]
        if available_only:
            slots = [s for s in slots if s["status"] == "available"]
        return sorted(slots, key=lambda x: (x["floor"], x["slot_number"]))

    def get_slot_by_id(self, slot_id: str) -> Optional[dict]:
        return self._demo_slots.get(slot_id)

    # ─── Parking CRUD (Admin) ─────────────────────────

    def create_parking(self, data: dict) -> dict:
        parking_id = f"parking_{uuid.uuid4().hex[:8]}"
        total_slots = data.get("total_slots", 20)
        parking = {
            "id": parking_id,
            "name": data["name"],
            "description": data.get("description", ""),
            "location": {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "address": data["address"],
                "city": data.get("city"),
                "country": data.get("country", "Egypt")
            },
            "parking_type": data.get("parking_type", "covered"),
            "total_slots": total_slots,
            "available_slots": total_slots,
            "occupied_slots": 0,
            "rate_per_hour": data["rate_per_hour"],
            "currency": data.get("currency", "EGP"),
            "amenities": data.get("amenities", []),
            "images": [],
            "rating": 0.0,
            "review_count": 0,
            "is_24_7": data.get("is_24_7", True),
            "is_active": True
        }
        self._demo_parkings[parking_id] = parking

        # Generate slots
        for i in range(total_slots):
            floor = (i // 20) + 1
            section = chr(65 + (i // 10) % 3)
            slot_num = (i % 10) + 1
            slot_number = f"{section}{slot_num:02d}"
            slot_id = f"{parking_id}_slot_{slot_number}"
            self._demo_slots[slot_id] = {
                "id": slot_id,
                "parking_id": parking_id,
                "slot_number": slot_number,
                "floor": floor,
                "section": section,
                "status": "available",
                "is_handicap": i % 10 == 0,
                "is_ev_charging": i % 15 == 0,
                "current_vehicle_plate": None
            }

        return parking

    def update_parking(self, parking_id: str, data: dict) -> Optional[dict]:
        parking = self._demo_parkings.get(parking_id)
        if not parking:
            return None

        if data.get("name") is not None:
            parking["name"] = data["name"]
        if data.get("description") is not None:
            parking["description"] = data["description"]
        if data.get("latitude") is not None:
            parking["location"]["latitude"] = data["latitude"]
        if data.get("longitude") is not None:
            parking["location"]["longitude"] = data["longitude"]
        if data.get("address") is not None:
            parking["location"]["address"] = data["address"]
        if data.get("city") is not None:
            parking["location"]["city"] = data["city"]
        if data.get("parking_type") is not None:
            parking["parking_type"] = data["parking_type"]
        if data.get("rate_per_hour") is not None:
            parking["rate_per_hour"] = data["rate_per_hour"]
        if data.get("amenities") is not None:
            parking["amenities"] = data["amenities"]
        if data.get("is_24_7") is not None:
            parking["is_24_7"] = data["is_24_7"]
        if data.get("is_active") is not None:
            parking["is_active"] = data["is_active"]

        return parking

    def delete_parking(self, parking_id: str) -> bool:
        if parking_id not in self._demo_parkings:
            return False
        # Soft delete - deactivate
        self._demo_parkings[parking_id]["is_active"] = False
        return True

    # ─── Spot Availability Watchers ───────────────────

    def add_spot_watcher(self, parking_id: str, user_id: str) -> bool:
        if parking_id not in self._demo_parkings:
            return False
        if not hasattr(self, '_spot_watchers'):
            self._spot_watchers = {}
        if parking_id not in self._spot_watchers:
            self._spot_watchers[parking_id] = set()
        self._spot_watchers[parking_id].add(user_id)
        return True

    def remove_spot_watcher(self, parking_id: str, user_id: str) -> bool:
        if not hasattr(self, '_spot_watchers'):
            return False
        if parking_id not in self._spot_watchers:
            return False
        self._spot_watchers[parking_id].discard(user_id)
        return True

    def get_spot_watchers(self, parking_id: str) -> List[str]:
        if not hasattr(self, '_spot_watchers'):
            return []
        return list(self._spot_watchers.get(parking_id, []))

    def is_watching(self, parking_id: str, user_id: str) -> bool:
        if not hasattr(self, '_spot_watchers'):
            return False
        return user_id in self._spot_watchers.get(parking_id, set())


class BookingService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def create_booking(self, user_id: str, data: dict) -> dict:
        parking = self.ps.get_parking_by_id(data["parking_id"])
        slot = self.ps.get_slot_by_id(data["slot_id"])
        if not parking or not slot:
            raise ValueError("Parking or slot not found")
        if slot["status"] != "available":
            raise ValueError("Slot not available")

        hours = (data["end_time"] - data["start_time"]).total_seconds() / 3600
        amount = hours * parking["rate_per_hour"]
        fees = amount * 0.05

        booking_id = f"booking_{uuid.uuid4().hex[:8]}"
        booking = {
            "id": booking_id,
            "user_id": user_id,
            "parking_id": parking["id"],
            "parking_name": parking["name"],
            "parking_address": parking["location"]["address"],
            "slot_id": slot["id"],
            "slot_number": slot["slot_number"],
            "floor": slot["floor"],
            "section": slot.get("section"),
            "vehicle_plate": data["vehicle_plate"],
            "start_time": data["start_time"].isoformat(),
            "end_time": data["end_time"].isoformat(),
            "actual_exit_time": None,
            "status": "confirmed",
            "total_hours": round(hours, 2),
            "amount": round(amount, 2),
            "fees": round(fees, 2),
            "total_amount": round(amount + fees, 2),
            "currency": parking["currency"],
            "payment_status": "completed",
            "payment_method": data.get("payment_method", "card"),
            "created_at": datetime.utcnow().isoformat()
        }

        self.ps._demo_slots[slot["id"]]["status"] = "reserved"
        self.ps._demo_parkings[parking["id"]]["available_slots"] -= 1
        self.ps._demo_parkings[parking["id"]]["occupied_slots"] += 1
        self.ps._demo_bookings[booking_id] = booking

        # Create notification for booking
        notif_service = get_notification_service()
        notif_service.create_notification(
            user_id=user_id,
            title="Booking Successful!",
            message=f"You have successfully booked slot {slot['slot_number']} at {parking['name']} for {round(hours, 1)} hours.",
            notification_type="booking",
            data={"booking_id": booking_id}
        )
        notif_service.create_notification(
            user_id=user_id,
            title="Payment Confirmed",
            message=f"Payment of {round(amount + fees, 2)} {parking['currency']} was successful via {data.get('payment_method', 'card')}.",
            notification_type="payment",
            data={"amount": round(amount + fees, 2), "booking_id": booking_id}
        )

        return booking

    def get_user_bookings(self, user_id: str) -> List[dict]:
        return [b for b in self.ps._demo_bookings.values() if b["user_id"] == user_id]

    def get_booking_history(self, user_id: str) -> List[dict]:
        return [
            b for b in self.ps._demo_bookings.values()
            if b["user_id"] == user_id and b["status"] in ["completed", "cancelled"]
        ]

    def get_active_booking(self, user_id: str) -> Optional[dict]:
        now = datetime.utcnow()
        for b in self.ps._demo_bookings.values():
            if b["user_id"] != user_id or b["status"] not in ["confirmed", "active"]:
                continue
            end = datetime.fromisoformat(b["end_time"].replace("Z", ""))
            if end > now:
                return {
                    "id": b["id"],
                    "parking_name": b["parking_name"],
                    "parking_address": b["parking_address"],
                    "slot_id": b["slot_id"],
                    "slot_number": b["slot_number"],
                    "floor": b["floor"],
                    "remaining_time_seconds": int((end - now).total_seconds()),
                    "start_time": b["start_time"],
                    "end_time": b["end_time"]
                }
        return None

    def get_booking_by_id(self, booking_id: str) -> Optional[dict]:
        return self.ps._demo_bookings.get(booking_id)

    def cancel_booking(self, booking_id: str, user_id: str) -> dict:
        b = self.ps._demo_bookings.get(booking_id)
        if not b:
            raise ValueError("Booking not found")
        if b["user_id"] != user_id:
            raise ValueError("Unauthorized")
        if b["status"] not in ["pending", "confirmed"]:
            raise ValueError("Cannot cancel")

        b["status"] = "cancelled"
        b["payment_status"] = "refunded"

        if b["slot_id"] in self.ps._demo_slots:
            self.ps._demo_slots[b["slot_id"]]["status"] = "available"
        if b["parking_id"] in self.ps._demo_parkings:
            self.ps._demo_parkings[b["parking_id"]]["available_slots"] += 1
            self.ps._demo_parkings[b["parking_id"]]["occupied_slots"] -= 1

        notif_service = get_notification_service()
        notif_service.create_notification(
            user_id=user_id,
            title="Booking Cancelled",
            message=f"Your booking at {b['parking_name']} has been cancelled. Refund of {b['total_amount']} {b['currency']} is being processed.",
            notification_type="booking",
            data={"booking_id": booking_id}
        )

        return b

    def extend_booking(self, booking_id: str, user_id: str, additional_hours: float) -> dict:
        b = self.ps._demo_bookings.get(booking_id)
        if not b:
            raise ValueError("Booking not found")
        if b["user_id"] != user_id:
            raise ValueError("Unauthorized")
        if b["status"] not in ["confirmed", "active"]:
            raise ValueError("Cannot extend this booking")

        parking = self.ps.get_parking_by_id(b["parking_id"])
        if not parking:
            raise ValueError("Parking not found")

        old_end = datetime.fromisoformat(b["end_time"].replace("Z", ""))
        new_end = old_end + timedelta(hours=additional_hours)
        extra_amount = additional_hours * parking["rate_per_hour"]
        extra_fees = extra_amount * 0.05

        b["end_time"] = new_end.isoformat()
        b["total_hours"] = round(b["total_hours"] + additional_hours, 2)
        b["amount"] = round(b["amount"] + extra_amount, 2)
        b["fees"] = round(b["fees"] + extra_fees, 2)
        b["total_amount"] = round(b["total_amount"] + extra_amount + extra_fees, 2)

        return b

    def find_booking_by_plate(self, parking_id: str, vehicle_plate: str,
                              statuses: Optional[List[str]] = None) -> Optional[dict]:
        """Find a booking matching a vehicle plate at a specific parking."""
        if statuses is None:
            statuses = ["confirmed", "active"]
        for b in self.ps._demo_bookings.values():
            if (b["parking_id"] == parking_id and
                    b["vehicle_plate"] == vehicle_plate and
                    b["status"] in statuses):
                return b
        return None

    def check_in(self, booking_id: str) -> Optional[dict]:
        """Check in: move confirmed → active, record actual entry time."""
        b = self.ps._demo_bookings.get(booking_id)
        if not b:
            return None
        if b["status"] != "confirmed":
            return None

        b["status"] = "active"
        b["actual_entry_time"] = datetime.utcnow().isoformat()

        # Mark slot as occupied
        if b["slot_id"] in self.ps._demo_slots:
            self.ps._demo_slots[b["slot_id"]]["status"] = "occupied"
            self.ps._demo_slots[b["slot_id"]]["current_vehicle_plate"] = b["vehicle_plate"]

        notif_service = get_notification_service()
        notif_service.create_notification(
            user_id=b["user_id"],
            title="Welcome! You've Checked In",
            message=f"You have entered {b['parking_name']}. Slot {b['slot_number']} is ready for you.",
            notification_type="booking",
            data={"booking_id": booking_id}
        )

        return b

    def check_out(self, booking_id: str) -> Optional[dict]:
        """Check out: move active → completed, calculate final price."""
        b = self.ps._demo_bookings.get(booking_id)
        if not b:
            return None
        if b["status"] != "active":
            return None

        now = datetime.utcnow()
        b["status"] = "completed"
        b["actual_exit_time"] = now.isoformat()

        # Calculate actual duration and adjust price if overstayed
        entry_time = datetime.fromisoformat(b.get("actual_entry_time", b["start_time"]).replace("Z", ""))
        actual_hours = (now - entry_time).total_seconds() / 3600
        booked_hours = b["total_hours"]

        if actual_hours > booked_hours:
            parking = self.ps.get_parking_by_id(b["parking_id"])
            if parking:
                extra_hours = actual_hours - booked_hours
                extra_amount = extra_hours * parking["rate_per_hour"]
                extra_fees = extra_amount * 0.05
                b["total_hours"] = round(actual_hours, 2)
                b["amount"] = round(b["amount"] + extra_amount, 2)
                b["fees"] = round(b["fees"] + extra_fees, 2)
                b["total_amount"] = round(b["total_amount"] + extra_amount + extra_fees, 2)

        # Free up the slot
        if b["slot_id"] in self.ps._demo_slots:
            self.ps._demo_slots[b["slot_id"]]["status"] = "available"
            self.ps._demo_slots[b["slot_id"]]["current_vehicle_plate"] = None
        if b["parking_id"] in self.ps._demo_parkings:
            self.ps._demo_parkings[b["parking_id"]]["available_slots"] += 1
            self.ps._demo_parkings[b["parking_id"]]["occupied_slots"] -= 1

        notif_service = get_notification_service()
        notif_service.create_notification(
            user_id=b["user_id"],
            title="Trip Complete!",
            message=f"You've checked out from {b['parking_name']}. Total: {b['total_amount']} {b['currency']}.",
            notification_type="payment",
            data={"booking_id": booking_id, "total_amount": b["total_amount"]}
        )

        return b

    def get_booking_qr(self, booking_id: str, user_id: str) -> Optional[dict]:
        b = self.ps._demo_bookings.get(booking_id)
        if not b or b["user_id"] != user_id:
            return None

        qr_data = json.dumps({
            "booking_id": b["id"],
            "parking_id": b["parking_id"],
            "slot": b["slot_number"],
            "plate": b["vehicle_plate"],
            "valid_from": b["start_time"],
            "valid_until": b["end_time"],
            "checksum": hashlib.md5(b["id"].encode()).hexdigest()[:8]
        })

        return {
            "booking_id": b["id"],
            "qr_data": qr_data,
            "parking_name": b["parking_name"],
            "slot_number": b["slot_number"],
            "start_time": b["start_time"],
            "end_time": b["end_time"],
            "vehicle_plate": b["vehicle_plate"]
        }


class AuthService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_user_by_email(self, email: str) -> Optional[dict]:
        for u in self.ps._demo_users.values():
            if u["email"] == email:
                return u
        return None

    def get_user_by_phone(self, phone: str) -> Optional[dict]:
        for u in self.ps._demo_users.values():
            if u.get("phone") and u["phone"].replace(" ", "") == phone.replace(" ", ""):
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        return self.ps._demo_users.get(user_id)

    def create_user(self, email: str, name: str, password_hash: str, phone: Optional[str] = None) -> dict:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "first_name": None,
            "last_name": None,
            "role": "user",
            "password_hash": password_hash,
            "is_active": True,
            "phone": phone,
            "gender": None,
            "address": None,
            "profile_photo": None,
            "cars": [],
            "payment_methods": [],
            "favorites": [],
            "created_at": datetime.utcnow().isoformat()
        }
        self.ps._demo_users[user_id] = user
        return user

    def social_login(self, provider: str, token: str, name: Optional[str] = None, email: Optional[str] = None) -> dict:
        if email:
            existing = self.get_user_by_email(email)
            if existing:
                return existing

        if not email:
            email = f"{provider}_{uuid.uuid4().hex[:8]}@parkify.social"
        if not name:
            name = f"{provider.title()} User"

        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "first_name": name.split()[0] if name else None,
            "last_name": name.split()[-1] if name and len(name.split()) > 1 else None,
            "role": "user",
            "password_hash": "",
            "is_active": True,
            "phone": None,
            "gender": None,
            "address": None,
            "profile_photo": None,
            "social_provider": provider,
            "cars": [],
            "payment_methods": [],
            "favorites": [],
            "created_at": datetime.utcnow().isoformat()
        }
        self.ps._demo_users[user_id] = user
        return user

    def generate_verification_code(self, identifier: str) -> str:
        code = f"{random.randint(100000, 999999)}"
        self.ps._verification_codes[identifier] = {
            "code": code,
            "expires": datetime.utcnow() + timedelta(minutes=10),
            "verified": False
        }
        return code

    def verify_code(self, identifier: str, code: str) -> bool:
        stored = self.ps._verification_codes.get(identifier)
        if not stored:
            return False
        if stored["expires"] < datetime.utcnow():
            return False
        if stored["code"] != code:
            return False
        stored["verified"] = True
        return True

    def generate_reset_code(self, identifier: str) -> str:
        code = f"{random.randint(100000, 999999)}"
        self.ps._reset_codes[identifier] = {
            "code": code,
            "expires": datetime.utcnow() + timedelta(minutes=15)
        }
        return code

    def verify_reset_code(self, identifier: str, code: str) -> bool:
        stored = self.ps._reset_codes.get(identifier)
        if not stored:
            return False
        if stored["expires"] < datetime.utcnow():
            return False
        if stored["code"] != code:
            return False
        return True

    def reset_password(self, identifier: str, new_password_hash: str) -> bool:
        user = self.get_user_by_email(identifier) or self.get_user_by_phone(identifier)
        if not user:
            return False
        user["password_hash"] = new_password_hash
        if identifier in self.ps._reset_codes:
            del self.ps._reset_codes[identifier]
        return True

    def update_profile(self, user_id: str, data: dict) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        if data.get("first_name") is not None:
            user["first_name"] = data["first_name"]
        if data.get("last_name") is not None:
            user["last_name"] = data["last_name"]
        if data.get("first_name") is not None or data.get("last_name") is not None:
            fn = user.get("first_name") or ""
            ln = user.get("last_name") or ""
            user["name"] = f"{fn} {ln}".strip()
        if data.get("phone") is not None:
            user["phone"] = data["phone"]
        if data.get("address") is not None:
            user["address"] = data["address"]
        if data.get("email") is not None:
            user["email"] = data["email"]
        if data.get("gender") is not None:
            user["gender"] = data["gender"]
        if data.get("profile_photo") is not None:
            user["profile_photo"] = data["profile_photo"]

        return user

    def complete_profile(self, user_id: str, data: dict) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        user["first_name"] = data.get("first_name")
        user["last_name"] = data.get("last_name")
        user["name"] = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        if data.get("gender"):
            user["gender"] = data["gender"]
        if data.get("phone"):
            user["phone"] = data["phone"]
        if data.get("address"):
            user["address"] = data["address"]

        if data.get("car_plate"):
            car_id = f"car_{uuid.uuid4().hex[:8]}"
            car = {
                "id": car_id,
                "license_plate": data["car_plate"],
                "make": None,
                "model": data.get("car_model"),
                "color": None,
                "is_default": len(user["cars"]) == 0
            }
            user["cars"].append(car)

        return user

    def change_password(self, user_id: str, current_hash: str, new_hash: str, verify_current) -> bool:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return False
        if not verify_current(current_hash, user["password_hash"]):
            return False
        user["password_hash"] = new_hash
        return True


class CarService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_user_cars(self, user_id: str) -> List[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return []
        return user.get("cars", [])

    def add_car(self, user_id: str, data: dict) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        car_id = f"car_{uuid.uuid4().hex[:8]}"
        car = {
            "id": car_id,
            "license_plate": data["license_plate"],
            "make": data.get("make"),
            "model": data.get("model"),
            "color": data.get("color"),
            "is_default": data.get("is_default", False)
        }

        if car["is_default"]:
            for c in user["cars"]:
                c["is_default"] = False

        if len(user["cars"]) == 0:
            car["is_default"] = True

        user["cars"].append(car)
        return car

    def update_car(self, user_id: str, car_id: str, data: dict) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        for car in user["cars"]:
            if car["id"] == car_id:
                if data.get("license_plate") is not None:
                    car["license_plate"] = data["license_plate"]
                if data.get("make") is not None:
                    car["make"] = data["make"]
                if data.get("model") is not None:
                    car["model"] = data["model"]
                if data.get("color") is not None:
                    car["color"] = data["color"]
                return car
        return None

    def delete_car(self, user_id: str, car_id: str) -> bool:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return False

        for i, car in enumerate(user["cars"]):
            if car["id"] == car_id:
                was_default = car["is_default"]
                user["cars"].pop(i)
                if was_default and user["cars"]:
                    user["cars"][0]["is_default"] = True
                return True
        return False

    def set_default_car(self, user_id: str, car_id: str) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        target = None
        for car in user["cars"]:
            car["is_default"] = car["id"] == car_id
            if car["id"] == car_id:
                target = car
        return target


class PaymentMethodService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_user_methods(self, user_id: str) -> List[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return []
        return user.get("payment_methods", [])

    def add_method(self, user_id: str, data: dict) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        pm_id = f"pm_{uuid.uuid4().hex[:8]}"
        last_four = None
        if data.get("card_number"):
            last_four = data["card_number"][-4:]

        expiry = None
        if data.get("expiry_month") and data.get("expiry_year"):
            expiry = f"{data['expiry_month']:02d}/{str(data['expiry_year'])[-2:]}"

        pm = {
            "id": pm_id,
            "method_type": data.get("method_type", "card"),
            "last_four": last_four,
            "card_holder": data.get("card_holder"),
            "expiry": expiry,
            "is_default": data.get("is_default", False)
        }

        if pm["is_default"]:
            for m in user["payment_methods"]:
                m["is_default"] = False

        if len(user["payment_methods"]) == 0:
            pm["is_default"] = True

        user["payment_methods"].append(pm)
        return pm

    def delete_method(self, user_id: str, method_id: str) -> bool:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return False

        for i, pm in enumerate(user["payment_methods"]):
            if pm["id"] == method_id:
                was_default = pm["is_default"]
                user["payment_methods"].pop(i)
                if was_default and user["payment_methods"]:
                    user["payment_methods"][0]["is_default"] = True
                return True
        return False

    def set_default_method(self, user_id: str, method_id: str) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return None

        target = None
        for pm in user["payment_methods"]:
            pm["is_default"] = pm["id"] == method_id
            if pm["id"] == method_id:
                target = pm
        return target


class NotificationService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_user_notifications(self, user_id: str) -> List[dict]:
        notifs = [n for n in self.ps._notifications.values() if n["user_id"] == user_id]
        return sorted(notifs, key=lambda x: x["created_at"], reverse=True)

    def get_unread_count(self, user_id: str) -> int:
        return sum(1 for n in self.ps._notifications.values()
                   if n["user_id"] == user_id and not n["is_read"])

    def mark_as_read(self, notification_id: str, user_id: str) -> Optional[dict]:
        n = self.ps._notifications.get(notification_id)
        if not n or n["user_id"] != user_id:
            return None
        n["is_read"] = True
        return n

    def mark_all_read(self, user_id: str) -> int:
        count = 0
        for n in self.ps._notifications.values():
            if n["user_id"] == user_id and not n["is_read"]:
                n["is_read"] = True
                count += 1
        return count

    def create_notification(self, user_id: str, title: str, message: str,
                            notification_type: str = "system", data: Optional[dict] = None) -> dict:
        notif_id = f"notif_{uuid.uuid4().hex[:8]}"
        notif = {
            "id": notif_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "is_read": False,
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        }
        self.ps._notifications[notif_id] = notif
        return notif

    def broadcast_notification(self, title: str, message: str,
                               notification_type: str = "system", data: Optional[dict] = None) -> int:
        count = 0
        for user_id in self.ps._demo_users:
            self.create_notification(user_id, title, message, notification_type, data)
            count += 1
        return count

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        n = self.ps._notifications.get(notification_id)
        if not n or n["user_id"] != user_id:
            return False
        del self.ps._notifications[notification_id]
        return True


class FavoriteService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_user_favorites(self, user_id: str) -> List[dict]:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return []

        results = []
        for parking_id in user.get("favorites", []):
            parking = self.ps._demo_parkings.get(parking_id)
            if parking:
                results.append({
                    "id": f"fav_{user_id}_{parking_id}",
                    "user_id": user_id,
                    "parking_id": parking_id,
                    "parking": parking,
                    "created_at": datetime.utcnow().isoformat()
                })
        return results

    def add_favorite(self, user_id: str, parking_id: str) -> Optional[dict]:
        user = self.ps._demo_users.get(user_id)
        parking = self.ps._demo_parkings.get(parking_id)
        if not user or not parking:
            return None

        if parking_id not in user.get("favorites", []):
            if "favorites" not in user:
                user["favorites"] = []
            user["favorites"].append(parking_id)

        return {
            "id": f"fav_{user_id}_{parking_id}",
            "user_id": user_id,
            "parking_id": parking_id,
            "parking": parking,
            "created_at": datetime.utcnow().isoformat()
        }

    def remove_favorite(self, user_id: str, parking_id: str) -> bool:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return False
        if parking_id in user.get("favorites", []):
            user["favorites"].remove(parking_id)
            return True
        return False

    def is_favorited(self, user_id: str, parking_id: str) -> bool:
        user = self.ps._demo_users.get(user_id)
        if not user:
            return False
        return parking_id in user.get("favorites", [])


class SupportService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def create_ticket(self, user_id: str, data: dict) -> dict:
        ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"
        ticket = {
            "id": ticket_id,
            "user_id": user_id,
            "subject": data["subject"],
            "message": data["message"],
            "category": data.get("category", "general"),
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }
        self.ps._support_tickets[ticket_id] = ticket
        return ticket

    def get_user_tickets(self, user_id: str) -> List[dict]:
        return sorted(
            [t for t in self.ps._support_tickets.values() if t["user_id"] == user_id],
            key=lambda x: x["created_at"],
            reverse=True
        )

    def get_all_tickets(self) -> List[dict]:
        return sorted(
            list(self.ps._support_tickets.values()),
            key=lambda x: x["created_at"],
            reverse=True
        )

    def update_ticket_status(self, ticket_id: str, status: str) -> Optional[dict]:
        ticket = self.ps._support_tickets.get(ticket_id)
        if not ticket:
            return None
        ticket["status"] = status
        ticket["updated_at"] = datetime.utcnow().isoformat()
        return ticket


class AlertService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_all_alerts(self, status: Optional[str] = None) -> List[dict]:
        alerts = list(self.ps._alerts.values())
        if status:
            alerts = [a for a in alerts if a["status"] == status]
        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

    def get_alert_by_id(self, alert_id: str) -> Optional[dict]:
        return self.ps._alerts.get(alert_id)

    def resolve_alert(self, alert_id: str, admin_id: str) -> Optional[dict]:
        alert = self.ps._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.utcnow().isoformat()
        alert["resolved_by"] = admin_id
        return alert

    def acknowledge_alert(self, alert_id: str) -> Optional[dict]:
        alert = self.ps._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = "acknowledged"
        return alert

    def create_alert(self, parking_id: str, alert_type: str, severity: str, message: str) -> dict:
        parking = self.ps._demo_parkings.get(parking_id)
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        alert = {
            "id": alert_id,
            "parking_id": parking_id,
            "parking_name": parking["name"] if parking else "Unknown",
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolved_by": None
        }
        self.ps._alerts[alert_id] = alert
        return alert


class VehicleLogService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service

    def get_logs(self, parking_id: Optional[str] = None, action: Optional[str] = None,
                 limit: int = 50) -> List[dict]:
        logs = list(self.ps._vehicle_logs.values())
        if parking_id:
            logs = [l for l in logs if l["parking_id"] == parking_id]
        if action:
            logs = [l for l in logs if l["action"] == action]
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    def add_log(self, parking_id: str, vehicle_plate: str, action: str,
                gate: str, confidence: Optional[float] = None) -> dict:
        parking = self.ps._demo_parkings.get(parking_id)
        log_id = f"vlog_{uuid.uuid4().hex[:8]}"
        log = {
            "id": log_id,
            "parking_id": parking_id,
            "parking_name": parking["name"] if parking else "Unknown",
            "vehicle_plate": vehicle_plate,
            "action": action,
            "gate": gate,
            "timestamp": datetime.utcnow().isoformat(),
            "plate_image": None,
            "confidence": confidence
        }
        self.ps._vehicle_logs[log_id] = log
        return log


# ─── Singletons ───────────────────────────────────────

_ps = None
_bs = None
_as = None
_cs = None
_pms = None
_ns = None
_fs = None
_ss = None
_als = None
_vls = None


def get_parking_service() -> ParkingService:
    global _ps
    if _ps is None:
        _ps = ParkingService()
    return _ps


def get_booking_service() -> BookingService:
    global _bs
    if _bs is None:
        _bs = BookingService(get_parking_service())
    return _bs


def get_auth_service() -> AuthService:
    global _as
    if _as is None:
        _as = AuthService(get_parking_service())
    return _as


def get_car_service() -> CarService:
    global _cs
    if _cs is None:
        _cs = CarService(get_parking_service())
    return _cs


def get_payment_method_service() -> PaymentMethodService:
    global _pms
    if _pms is None:
        _pms = PaymentMethodService(get_parking_service())
    return _pms


def get_notification_service() -> NotificationService:
    global _ns
    if _ns is None:
        _ns = NotificationService(get_parking_service())
    return _ns


def get_favorite_service() -> FavoriteService:
    global _fs
    if _fs is None:
        _fs = FavoriteService(get_parking_service())
    return _fs


def get_support_service() -> SupportService:
    global _ss
    if _ss is None:
        _ss = SupportService(get_parking_service())
    return _ss


def get_alert_service() -> AlertService:
    global _als
    if _als is None:
        _als = AlertService(get_parking_service())
    return _als


def get_vehicle_log_service() -> VehicleLogService:
    global _vls
    if _vls is None:
        _vls = VehicleLogService(get_parking_service())
    return _vls
