"""
Smart Doctor Connect AI — Pydantic Data Models
All request/response schemas live here. MongoDB _id is handled via aliases.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Shared Config ─────────────────────────────────────────────────────────────
class MongoBaseModel(BaseModel):
    """Base model that serialises MongoDB ObjectId correctly."""

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


# ── Enums ─────────────────────────────────────────────────────────────────────
class ConsultationType(str, Enum):
    online = "online"
    in_person = "in_person"
    both = "both"


# ── Doctor Models ─────────────────────────────────────────────────────────────
class DoctorCreate(MongoBaseModel):
    """Payload to register a new doctor."""

    name: str = Field(..., min_length=2, max_length=100, examples=["Dr. Sara Ahmed"])
    specialization: str = Field(..., min_length=2, max_length=100, examples=["Cardiologist"])
    location: str = Field(..., min_length=2, max_length=100, examples=["Lahore"])
    consultation_type: ConsultationType = ConsultationType.both
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+92\s?[0-9]{3}\s?[0-9]{7}$", examples=["+92 300 1234567"])
    bio: Optional[str] = Field(None, max_length=1000)
    experience_years: int = Field(..., ge=0, le=60)
    consultation_fee: int = Field(..., ge=0, description="Fee in PKR")
    # availability: { "Monday": ["09:00", "09:30"], "Wednesday": ["14:00"] }
    availability: Dict[str, List[str]] = Field(default_factory=dict)
    is_available: bool = True
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    total_reviews: int = Field(default=0, ge=0)

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        for day in v:
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}")
        return v


class DoctorInDB(DoctorCreate):
    """Doctor as stored in MongoDB (includes generated fields)."""

    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class DoctorResponse(DoctorInDB):
    """Doctor returned to the client — adds computed match_score for search results."""

    match_score: Optional[int] = Field(None, ge=0, le=100)


class DoctorUpdate(MongoBaseModel):
    """Partial update — all fields optional."""

    name: Optional[str] = None
    specialization: Optional[str] = None
    location: Optional[str] = None
    consultation_type: Optional[ConsultationType] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[int] = None
    availability: Optional[Dict[str, List[str]]] = None
    is_available: Optional[bool] = None
    phone: Optional[str] = None


# ── Appointment Models ────────────────────────────────────────────────────────
class AppointmentStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class AppointmentCreate(MongoBaseModel):
    """Payload to book a new appointment."""

    doctor_id: str
    doctor_name: str
    patient_name: str = Field(..., min_length=2, max_length=100)
    patient_contact: str = Field(..., pattern=r"^\+92\s?[0-9]{3}\s?[0-9]{7}$")
    patient_email: EmailStr
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2025-01-15"])
    time_slot: str = Field(..., pattern=r"^\d{2}:\d{2}$", examples=["10:00"])
    consultation_type: ConsultationType
    symptoms: Optional[str] = Field(None, max_length=500)


class AppointmentInDB(AppointmentCreate):
    """Appointment as stored in MongoDB."""

    id: Optional[str] = Field(None, alias="_id")
    status: AppointmentStatus = AppointmentStatus.confirmed
    queue_position: int = Field(default=1, ge=1)
    predicted_wait_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class AppointmentStatusUpdate(MongoBaseModel):
    status: AppointmentStatus


# ── Chat / Message Models ─────────────────────────────────────────────────────
class MessageCreate(MongoBaseModel):
    doctor_id: str
    patient_name: str = Field(..., min_length=1, max_length=100)
    patient_contact: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)


class MessageInDB(MessageCreate):
    id: Optional[str] = Field(None, alias="_id")
    ai_response: str
    doctor_available: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ── AI Search Models ──────────────────────────────────────────────────────────
class UrgencyLevel(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    emergency = "EMERGENCY"


class AISearchResult(MongoBaseModel):
    """Structured output from the symptom analysis engine."""

    specializations: List[str]
    urgency: UrgencyLevel
    home_advice: str
    detected_location: Optional[str] = None
    doctors: List[DoctorResponse] = Field(default_factory=list)


# ── General Triage Assistant Models ──────────────────────────────────────────
class TriageMessageCreate(MongoBaseModel):
    patient_name: str
    message: str


class TriageMessageResponse(MongoBaseModel):
    ai_response: str
    specializations: List[str]
    urgency: UrgencyLevel
    home_advice: str
    doctors: List[DoctorResponse] = Field(default_factory=list)
