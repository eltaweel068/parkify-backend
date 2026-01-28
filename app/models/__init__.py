"""Pydantic Models"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SlotStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# User
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    role: str = "user"
    is_active: bool = True


class CarCreate(BaseModel):
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False


class CarResponse(BaseModel):
    id: str
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False


# Location
class Location(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: Optional[str] = None
    country: Optional[str] = None


# Parking
class ParkingSlot(BaseModel):
    id: str
    parking_id: str
    slot_number: str
    floor: int = 1
    section: Optional[str] = None
    status: SlotStatus = SlotStatus.AVAILABLE
    is_handicap: bool = False
    is_ev_charging: bool = False
    current_vehicle_plate: Optional[str] = None


class ParkingResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    location: Location
    parking_type: str = "covered"
    total_slots: int
    available_slots: int
    occupied_slots: int = 0
    rate_per_hour: float
    currency: str = "EGP"
    amenities: List[str] = []
    images: List[str] = []
    rating: float = 0.0
    review_count: int = 0
    is_24_7: bool = True
    is_active: bool = True
    distance_meters: Optional[float] = None
    walking_time_minutes: Optional[int] = None


# Booking
class BookingCreate(BaseModel):
    parking_id: str
    slot_id: str
    vehicle_plate: str
    start_time: datetime
    end_time: datetime
    payment_method: str = "card"


class BookingResponse(BaseModel):
    id: str
    user_id: str
    parking_id: str
    parking_name: str
    parking_address: str
    slot_id: str
    slot_number: str
    floor: int
    section: Optional[str] = None
    vehicle_plate: str
    start_time: datetime
    end_time: datetime
    actual_exit_time: Optional[datetime] = None
    status: BookingStatus
    total_hours: float
    amount: float
    fees: float
    total_amount: float
    currency: str = "EGP"
    payment_status: PaymentStatus
    payment_method: str
    created_at: datetime


class ActiveBookingResponse(BaseModel):
    id: str
    parking_name: str
    parking_address: str
    slot_id: str
    slot_number: str
    floor: int
    remaining_time_seconds: int
    start_time: datetime
    end_time: datetime


# Admin
class DashboardStats(BaseModel):
    total_parkings: int
    total_slots: int
    available_slots: int
    occupied_slots: int
    total_users: int
    active_bookings: int
    today_bookings: int
    today_revenue: float
    pending_alerts: int
    currency: str = "EGP"


class GateControlRequest(BaseModel):
    gate_type: str = "entry"
    action: str = "open"
    reason: Optional[str] = None
