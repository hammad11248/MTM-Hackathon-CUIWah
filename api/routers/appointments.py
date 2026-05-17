"""
Smart Doctor Connect AI — Appointments Router
Endpoints: book appointment, get available slots, update status.
Implements conflict-free booking via MongoDB unique index on (doctor_id, date, time_slot).
"""

from __future__ import annotations

from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pymongo.errors import DuplicateKeyError

from api.database import get_db
from api.models import (
    AppointmentCreate,
    AppointmentInDB,
    AppointmentStatusUpdate,
)
from api.services.email_service import send_appointment_confirmation

router = APIRouter()

AVG_CONSULTATION_MINUTES = 15  # average consultation duration for wait prediction


def _appt_to_response(doc: dict) -> AppointmentInDB:
    """Convert a MongoDB appointment document to an AppointmentInDB response."""
    doc["_id"] = str(doc["_id"])
    return AppointmentInDB(**doc)


# ── Book Appointment ──────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=AppointmentInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new appointment",
)
async def book_appointment(payload: AppointmentCreate):
    db = await get_db()

    # Verify doctor exists
    try:
        doctor_oid = ObjectId(payload.doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    doctor = await db.doctors.find_one({"_id": doctor_oid})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    # Calculate queue position: count existing appointments for that doctor+date
    existing_count = await db.appointments.count_documents(
        {
            "doctor_id": payload.doctor_id,
            "date": payload.date,
            "status": {"$in": ["confirmed", "pending"]},
        }
    )
    queue_position = existing_count + 1
    predicted_wait = (queue_position - 1) * AVG_CONSULTATION_MINUTES

    # Build the appointment document
    appt_dict = payload.model_dump()
    appt_dict["status"] = "confirmed"
    appt_dict["queue_position"] = queue_position
    appt_dict["predicted_wait_minutes"] = predicted_wait

    # Insert — unique index on (doctor_id, date, time_slot) prevents double-booking
    try:
        result = await db.appointments.insert_one(appt_dict)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked. Please choose a different slot.",
        )

    created = await db.appointments.find_one({"_id": result.inserted_id})

    # Send confirmation email (simulated)
    await send_appointment_confirmation(
        patient_email=payload.patient_email,
        patient_name=payload.patient_name,
        doctor_name=payload.doctor_name,
        date=payload.date,
        time_slot=payload.time_slot,
        consultation_type=payload.consultation_type,
        queue_position=queue_position,
        predicted_wait=predicted_wait,
    )

    return _appt_to_response(created)


# ── Get Available Slots ───────────────────────────────────────────────────────
@router.get(
    "/available-slots/{doctor_id}",
    summary="Get free time slots for a doctor on a specific date",
)
async def get_available_slots(
    doctor_id: str,
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format"),
):
    db = await get_db()

    # Fetch doctor to get their full availability
    try:
        doctor_oid = ObjectId(doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    doctor = await db.doctors.find_one({"_id": doctor_oid})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    # Determine the day of week from the date
    from datetime import datetime as dt

    try:
        date_obj = dt.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    day_name = date_obj.strftime("%A")  # e.g. "Monday"

    # Get all slots for that day from doctor's availability
    all_slots = doctor.get("availability", {}).get(day_name, [])

    # Get already-booked slots
    booked_cursor = db.appointments.find(
        {
            "doctor_id": doctor_id,
            "date": date,
            "status": {"$in": ["confirmed", "pending"]},
        },
        {"time_slot": 1},
    )
    booked_docs = await booked_cursor.to_list(length=100)
    booked_slots = {doc["time_slot"] for doc in booked_docs}

    # Compute free slots
    free_slots = [slot for slot in all_slots if slot not in booked_slots]

    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor.get("name", ""),
        "date": date,
        "day": day_name,
        "all_slots": all_slots,
        "booked_slots": list(booked_slots),
        "free_slots": free_slots,
        "total_booked": len(booked_slots),
    }


# ── Update Appointment Status ────────────────────────────────────────────────
@router.patch(
    "/{appointment_id}/status",
    response_model=AppointmentInDB,
    summary="Update appointment status",
)
async def update_appointment_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
):
    db = await get_db()

    try:
        oid = ObjectId(appointment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid appointment ID format.")

    result = await db.appointments.update_one(
        {"_id": oid},
        {"$set": {"status": payload.status.value}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    updated = await db.appointments.find_one({"_id": oid})
    return _appt_to_response(updated)


# ── Get Appointments by Doctor ────────────────────────────────────────────────
@router.get(
    "/doctor/{doctor_id}",
    response_model=List[AppointmentInDB],
    summary="Get all appointments for a doctor",
)
async def get_doctor_appointments(
    doctor_id: str,
    date: str = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    status_filter: str = Query(default=None, alias="status"),
):
    db = await get_db()

    query = {"doctor_id": doctor_id}
    if date:
        query["date"] = date
    if status_filter:
        query["status"] = status_filter

    cursor = db.appointments.find(query).sort("time_slot", 1)
    docs = await cursor.to_list(length=100)
    return [_appt_to_response(d) for d in docs]


# ── Get Appointments by Patient Email ─────────────────────────────────────────
@router.get(
    "/patient",
    response_model=List[AppointmentInDB],
    summary="Get all appointments for a patient",
)
async def get_patient_appointments(
    email: str = Query(..., description="Patient email address"),
):
    db = await get_db()
    cursor = db.appointments.find({"patient_email": email}).sort("date", -1)
    docs = await cursor.to_list(length=100)
    return [_appt_to_response(d) for d in docs]
