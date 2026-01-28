"""Services with Demo Data"""

from typing import List, Optional
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
import uuid


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
                "name": "Admin",
                "role": "admin",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VPMFFqhIuXbHKG",
                "is_active": True,
                "cars": []
            },
            "demo_user": {
                "id": "demo_user",
                "email": "user@parkify.com",
                "name": "Ahmed Mohamed",
                "role": "user",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VPMFFqhIuXbHKG",
                "is_active": True,
                "cars": [
                    {"id": "car_1", "license_plate": "أ ب ج 1234", "make": "Toyota", "model": "Corolla", "color": "White", "is_default": True}
                ]
            }
        }
    
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
    
    def get_parking_by_id(self, parking_id: str) -> Optional[dict]:
        return self._demo_parkings.get(parking_id)
    
    def get_parking_slots(self, parking_id: str, available_only: bool = False) -> List[dict]:
        slots = [s for s in self._demo_slots.values() if s["parking_id"] == parking_id]
        if available_only:
            slots = [s for s in slots if s["status"] == "available"]
        return sorted(slots, key=lambda x: (x["floor"], x["slot_number"]))
    
    def get_slot_by_id(self, slot_id: str) -> Optional[dict]:
        return self._demo_slots.get(slot_id)


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
        
        return booking
    
    def get_user_bookings(self, user_id: str) -> List[dict]:
        return [b for b in self.ps._demo_bookings.values() if b["user_id"] == user_id]
    
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
        
        return b


class AuthService:
    def __init__(self, parking_service: ParkingService):
        self.ps = parking_service
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        for u in self.ps._demo_users.values():
            if u["email"] == email:
                return u
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        return self.ps._demo_users.get(user_id)
    
    def create_user(self, email: str, name: str, password_hash: str) -> dict:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "role": "user",
            "password_hash": password_hash,
            "is_active": True,
            "cars": [],
            "created_at": datetime.utcnow().isoformat()
        }
        self.ps._demo_users[user_id] = user
        return user


# Singletons
_ps = None
_bs = None
_as = None

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
