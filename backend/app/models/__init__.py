import enum
import uuid
from datetime import date, datetime, time
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database.base import Base

settings = get_settings()


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    ADMIN = "admin"
    DOCTOR = "doctor"
    HOSPITAL_STAFF = "hospital_staff"


class SubscriptionPlan(str, enum.Enum):
    FREE_TRIAL = "free_trial"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UrgencyLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    name_kana: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    job_function: Mapped[Optional[str]] = mapped_column(String(255))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    medical_record_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="ja")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PATIENT)
    allergies: Mapped[Optional[str]] = mapped_column(Text)
    medical_history: Mapped[Optional[str]] = mapped_column(Text)
    profile_photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stored_assets.id", ondelete="SET NULL")
    )
    family_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    chat_cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="user")
    medical_records: Mapped[list["MedicalRecord"]] = relationship(back_populates="user")
    health_checkins: Mapped[list["HealthCheckin"]] = relationship(back_populates="user")
    conversation_memories: Mapped[list["ConversationMemory"]] = relationship(back_populates="user")
    symptom_assessments: Mapped[list["SymptomAssessment"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE_TRIAL)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500))
    name_en: Mapped[Optional[str]] = mapped_column(String(500))
    address: Mapped[str] = mapped_column(Text)
    prefecture: Mapped[str] = mapped_column(String(50), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    reservation_url: Mapped[Optional[str]] = mapped_column(String(500))
    hospital_type: Mapped[str] = mapped_column(String(50), index=True)
    departments: Mapped[list] = mapped_column(JSONB, default=list)
    insurance_accepted: Mapped[list] = mapped_column(JSONB, default=list)
    languages: Mapped[list] = mapped_column(JSONB, default=list)
    opening_hours: Mapped[Optional[dict]] = mapped_column(JSONB)
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    wheelchair_accessible: Mapped[bool] = mapped_column(Boolean, default=False)
    parking_available: Mapped[bool] = mapped_column(Boolean, default=False)
    accepting_new_patients: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    name: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[Optional[str]] = mapped_column(String(255))
    specialty: Mapped[str] = mapped_column(String(100), index=True)
    specialty_en: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    bio_en: Mapped[Optional[str]] = mapped_column(Text)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255))
    languages: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hospital: Mapped[Optional["Hospital"]] = relationship()
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="doctor")
    schedules: Mapped[list["DoctorSchedule"]] = relationship(back_populates="doctor")


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="schedules")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"))
    hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    time: Mapped[time] = mapped_column(Time)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    symptoms: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.PENDING, index=True
    )
    google_event_id: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    reminder_sent_1d: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_sent_1h: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="reservations")
    doctor: Mapped[Optional["Doctor"]] = relationship(back_populates="reservations")
    hospital: Mapped[Optional["Hospital"]] = relationship()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(50), default="line")
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="messages")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    visit_date: Mapped[date] = mapped_column(Date)
    symptoms: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis_notes: Mapped[Optional[str]] = mapped_column(Text)
    doctor_notes: Mapped[Optional[str]] = mapped_column(Text)
    prescriptions: Mapped[Optional[list]] = mapped_column(JSONB)
    lab_results: Mapped[Optional[dict]] = mapped_column(JSONB)
    hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="medical_records")


class HealthCheckin(Base):
    __tablename__ = "health_checkins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    checkin_date: Mapped[date] = mapped_column(Date, index=True)
    mood: Mapped[Optional[int]] = mapped_column(Integer)
    symptoms: Mapped[Optional[str]] = mapped_column(Text)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float)
    exercise_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    medication_taken: Mapped[Optional[bool]] = mapped_column(Boolean)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="health_checkins")


class ConversationMemory(Base):
    __tablename__ = "conversation_memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    key_facts: Mapped[Optional[list]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversation_memories")


class SymptomAssessment(Base):
    __tablename__ = "symptom_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    symptoms: Mapped[str] = mapped_column(Text)
    follow_up_responses: Mapped[Optional[dict]] = mapped_column(JSONB)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), default=UrgencyLevel.LOW)
    recommended_department: Mapped[Optional[str]] = mapped_column(String(100))
    recommended_tests: Mapped[Optional[list]] = mapped_column(JSONB)
    recommended_hospitals: Mapped[Optional[list]] = mapped_column(JSONB)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="This is not a medical diagnosis. Please consult a healthcare professional.",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="symptom_assessments")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(100), index=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stored_assets.id", ondelete="SET NULL")
    )
    content: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="ja")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    embedding = mapped_column(Vector(settings.EMBEDDING_DIMENSION))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(50), default="line")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notifications")


class AILog(Base):
    __tablename__ = "ai_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    agent: Mapped[Optional[str]] = mapped_column(String(100))
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    function_calls: Mapped[Optional[list]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text)
    question_en: Mapped[Optional[str]] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    answer_en: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="admin")
    hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
