from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    home_address: str = Field(..., min_length=5, description="Patient home address for hospital guidance")
    job_function: str = Field(..., min_length=1, description="Patient occupation/job function")
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


# Chat
class ChatRequest(BaseModel):
    message: str
    channel: str = "web"


class ChatResponse(BaseModel):
    reply: str
    user_id: str
    hospitals: list = []
    pharmacies: list = []
    specialists: list = []
    suggested_department: Optional[str] = None
    cannot_diagnose: bool = False
    show_hospital_finder: bool = False
    show_pharmacy_finder: bool = False
    plan: Optional[str] = None
    features: list[str] = []


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    created_at: str


class HospitalFilterRequest(BaseModel):
    symptoms: str = ""
    sort_by: str = "nearest"  # nearest | specialty | rating
    department: Optional[str] = None
    excellence_only: bool = False
    urgency: str = "low"
    language: str = "ja"
    limit: int = 10


class SymptomAssessmentRequest(BaseModel):
    symptoms: str


class SymptomAssessmentResponse(BaseModel):
    id: str
    urgency: str
    summary: str
    recommended_department: Optional[str] = None
    recommended_tests: Optional[list] = None
    disclaimer: str


# Reservation
class ReservationCreate(BaseModel):
    doctor_id: Optional[UUID] = None
    hospital_id: Optional[UUID] = None
    date: date
    time: str
    symptoms: Optional[str] = None
    department: Optional[str] = None


class ReservationResponse(BaseModel):
    id: UUID
    date: date
    time: str
    status: str
    department: Optional[str] = None
    symptoms: Optional[str] = None

    model_config = {"from_attributes": True}


class AvailabilityRequest(BaseModel):
    doctor_id: UUID
    date: date
    period: Optional[str] = None


# Hospital
class HospitalSearchRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 20
    department: Optional[str] = None
    emergency_only: bool = False
    language: Optional[str] = None


class HospitalResponse(BaseModel):
    id: Optional[UUID] = None
    name: str
    address: str
    distance_km: Optional[float] = None
    phone: Optional[str] = None
    departments: list = []
    emergency_available: bool = False
    rating: Optional[float] = None
    reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    directions_url: Optional[str] = None
    travel_time_minutes: Optional[int] = None
    route_summary: Optional[str] = None
    routes: Optional[dict] = None


class HospitalRecommendRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    symptoms: str
    urgency: str = "low"
    language: str = "ja"


# Health Check-in
class HealthCheckinCreate(BaseModel):
    mood: Optional[int] = Field(None, ge=1, le=5)
    symptoms: Optional[str] = None
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    sleep_hours: Optional[float] = None
    exercise_minutes: Optional[int] = None
    medication_taken: Optional[bool] = None
    notes: Optional[str] = None


# User
class UserProfile(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str = "ja"
    address: Optional[str] = None
    job_function: Optional[str] = None
    profile_photo_id: Optional[UUID] = None
    profile_photo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    job_function: Optional[str] = None
    preferred_language: Optional[str] = None
    allergies: Optional[str] = None


# Admin
class AdminDashboardStats(BaseModel):
    today_reservations: int
    total_patients: int
    active_subscriptions: int
    ai_calls_today: int
    unread_notifications: int


class FAQCreate(BaseModel):
    question: str
    question_en: Optional[str] = None
    answer: str
    answer_en: Optional[str] = None
    category: str


class AdminSubscriptionUpdate(BaseModel):
    plan: str
    admin_override: bool = True


class AdminSubscriptionCancel(BaseModel):
    at_period_end: bool = False


# RAG
class RAGQuery(BaseModel):
    query: str
    language: str = "ja"
    category: Optional[str] = None


class RAGIndexRequest(BaseModel):
    title: str
    content: str
    category: str
    language: str = "ja"
