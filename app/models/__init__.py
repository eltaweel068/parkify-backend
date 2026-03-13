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


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class NotificationType(str, Enum):
    BOOKING = "booking"
    PAYMENT = "payment"
    PROMO = "promo"
    SECURITY = "security"
    SYSTEM = "system"
    ALERT = "alert"


class AlertType(str, Enum):
    FIRE = "fire"
    THEFT = "theft"
    SYSTEM = "system"
    GATE = "gate"
    SECURITY = "security"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# ─── Auth ───────────────────────────────────────────────

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


class SocialLoginRequest(BaseModel):
    provider: str  # "google", "facebook", "apple"
    token: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordEmailRequest(BaseModel):
    email: EmailStr


class ForgotPasswordPhoneRequest(BaseModel):
    phone: str


class VerifyCodeRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str


class ResendCodeRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ─── User / Profile ────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    role: str = "user"
    is_active: bool = True


class UserProfileResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    profile_photo: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[str] = None


class CompleteProfileRequest(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[GenderEnum] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    car_plate: Optional[str] = None
    car_model: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[GenderEnum] = None


# ─── Cars ───────────────────────────────────────────────

class CarCreate(BaseModel):
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False


class CarUpdate(BaseModel):
    license_plate: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None


class CarResponse(BaseModel):
    id: str
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False


# ─── Location ──────────────────────────────────────────

class Location(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: Optional[str] = None
    country: Optional[str] = None


# ─── Parking ───────────────────────────────────────────

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
    is_favorited: Optional[bool] = None


class ParkingFilterRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: float = 10.0
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    parking_type: Optional[str] = None  # "covered", "uncovered", "multi_level"
    sort_by: str = "distance"  # "distance", "price", "rating"
    amenities: Optional[List[str]] = None
    available_only: bool = True


# ─── Booking ──────────────────────────────────────────

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


class BookingExtendRequest(BaseModel):
    additional_hours: float


class BookingQRResponse(BaseModel):
    booking_id: str
    qr_data: str
    parking_name: str
    slot_number: str
    start_time: str
    end_time: str
    vehicle_plate: str


# ─── Payment Methods ──────────────────────────────────

class PaymentMethodCreate(BaseModel):
    method_type: str = "card"  # "card", "apple_pay", "google_pay", "cash"
    card_number: Optional[str] = None
    card_holder: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False


class PaymentMethodResponse(BaseModel):
    id: str
    method_type: str
    last_four: Optional[str] = None
    card_holder: Optional[str] = None
    expiry: Optional[str] = None
    is_default: bool = False


# ─── Notifications ────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool = False
    data: Optional[dict] = None
    created_at: str


class UnreadCountResponse(BaseModel):
    count: int


# ─── Favorites ────────────────────────────────────────

class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    parking_id: str
    parking: ParkingResponse
    created_at: str


# ─── Support ──────────────────────────────────────────

class SupportTicketCreate(BaseModel):
    subject: str
    message: str
    category: str = "general"  # "general", "booking", "payment", "technical"


class SupportTicketResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    category: str
    status: str = "open"  # "open", "in_progress", "resolved", "closed"
    created_at: str
    updated_at: Optional[str] = None


# ─── Admin ────────────────────────────────────────────

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


class AlertResponse(BaseModel):
    id: str
    parking_id: str
    parking_name: str
    alert_type: AlertType
    severity: str  # "low", "medium", "high", "critical"
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


class VehicleLogResponse(BaseModel):
    id: str
    parking_id: str
    parking_name: str
    vehicle_plate: str
    action: str  # "entry", "exit"
    gate: str
    timestamp: str
    plate_image: Optional[str] = None
    confidence: Optional[float] = None


class AdminSendNotificationRequest(BaseModel):
    user_id: Optional[str] = None  # None = broadcast to all
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
