"""
Smart Doctor Connect AI — Chat Router
Endpoints: send message (AI receptionist), get chat history.
When a doctor is offline, the AI generates a response, stores the message,
sends an email notification, and schedules a follow-up reminder.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from api.database import get_db
from api.models import (
    MessageCreate,
    MessageInDB,
    TriageMessageCreate,
    TriageMessageResponse,
    DoctorResponse,
    UrgencyLevel,
)
from api.services.ai_agent import ai_agent
from api.services.recommender import SymptomRecommender
from api.services.email_service import (
    send_doctor_notification,
    send_followup_reminder,
)
from api.routers.doctors import PAKISTAN_CITIES

router = APIRouter()
recommender = SymptomRecommender()


def _msg_to_response(doc: dict) -> MessageInDB:
    """Convert a MongoDB message document to a MessageInDB response."""
    doc["_id"] = str(doc["_id"])
    return MessageInDB(**doc)


# ── Send Message (AI Receptionist) ────────────────────────────────────────────
@router.post(
    "/message",
    response_model=MessageInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to a doctor (AI responds if offline)",
)
async def send_message(payload: MessageCreate):
    db = get_db()

    # Verify doctor exists
    try:
        doctor_oid = ObjectId(payload.doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    doctor = await db.doctors.find_one({"_id": doctor_oid})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    doctor_name = doctor.get("name", "the doctor")
    doctor_email = doctor.get("email", "")
    doctor_available = doctor.get("is_available", False)

    # Generate AI response
    ai_response = await ai_agent.generate_response(
        patient_name=payload.patient_name,
        message=payload.message,
        doctor_name=doctor_name,
        doctor_available=doctor_available,
    )

    # Store message in database
    msg_dict = payload.model_dump()
    msg_dict["ai_response"] = ai_response
    msg_dict["doctor_available"] = doctor_available
    msg_dict["created_at"] = datetime.now(timezone.utc)

    result = await db.messages.insert_one(msg_dict)
    created = await db.messages.find_one({"_id": result.inserted_id})

    # If doctor is offline, send email notification and schedule follow-up
    if not doctor_available and doctor_email:
        await send_doctor_notification(
            doctor_email=doctor_email,
            doctor_name=doctor_name,
            patient_name=payload.patient_name,
            patient_contact=payload.patient_contact,
            message=payload.message,
        )

        # Schedule a follow-up reminder (using APScheduler if available)
        try:
            await _schedule_followup(
                patient_contact=payload.patient_contact,
                patient_name=payload.patient_name,
                doctor_name=doctor_name,
                original_message=payload.message,
            )
        except Exception:
            pass  # Non-critical — don't fail the request

    return _msg_to_response(created)


# ── Get Chat History ──────────────────────────────────────────────────────────
@router.get(
    "/history/{doctor_id}",
    response_model=List[MessageInDB],
    summary="Get chat history for a doctor",
)
async def get_chat_history(doctor_id: str, limit: int = 50):
    db = get_db()

    # Verify doctor exists
    try:
        ObjectId(doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    cursor = (
        db.messages.find({"doctor_id": doctor_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)

    # Return in chronological order (oldest first)
    docs.reverse()
    return [_msg_to_response(d) for d in docs]


# ── Follow-up Scheduler ──────────────────────────────────────────────────────
async def _schedule_followup(
    patient_contact: str | None,
    patient_name: str,
    doctor_name: str,
    original_message: str,
) -> None:
    """
    Schedule a follow-up reminder 4 hours after the initial message.
    Uses APScheduler for async job scheduling.
    If APScheduler is unavailable, logs and skips gracefully.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.date import DateTrigger

        scheduler = AsyncIOScheduler()
        run_time = datetime.now(timezone.utc) + timedelta(hours=4)

        scheduler.add_job(
            send_followup_reminder,
            trigger=DateTrigger(run_date=run_time),
            kwargs={
                "patient_email": patient_contact or "",
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "original_message": original_message,
            },
            id=f"followup_{patient_name}_{datetime.now(timezone.utc).timestamp()}",
            replace_existing=True,
        )

        if not scheduler.running:
            scheduler.start()

        print(
            f"⏰ Follow-up reminder scheduled for {patient_name} "
            f"regarding {doctor_name} at {run_time.isoformat()}"
        )
    except Exception as e:
        print(f"⚠️ Could not schedule follow-up (non-critical): {e}")


# ── Triage Helpers ────────────────────────────────────────────────────────────
def _detect_location(text: str) -> Optional[str]:
    """Extract Pakistani city names from text."""
    lower = text.lower()
    for city in PAKISTAN_CITIES:
        if city in lower:
            return city.title()
    return None


def _score_doctor(doc: dict, specializations: List[str], location: Optional[str]) -> int:
    """Score matching doctor out of 100."""
    score = 0
    doc_spec = doc.get("specialization", "").lower()

    for spec in specializations:
        if spec.lower() in doc_spec or doc_spec in spec.lower():
            score += 50
            break

    if location and location.lower() in doc.get("location", "").lower():
        score += 30

    if doc.get("is_available"):
        score += 10

    rating = doc.get("rating", 0.0)
    score += min(10, int(rating * 2))

    return min(score, 100)


def _doc_to_response(doc: dict, match_score: Optional[int] = None) -> DoctorResponse:
    doc["_id"] = str(doc["_id"])
    return DoctorResponse(**doc, match_score=match_score)


# ── Interactive Triage Assistant Endpoint ──────────────────────────────────────
@router.post(
    "/triage",
    response_model=TriageMessageResponse,
    summary="Interactive home page symptom triage chat assistant",
)
async def triage_message(payload: TriageMessageCreate):
    db = get_db()
    
    # 1. Analyse symptoms using recommender
    analysis = await recommender.analyse(payload.message)
    specializations: List[str] = analysis["specializations"]
    urgency: UrgencyLevel = UrgencyLevel(analysis["urgency"].upper())
    home_advice: str = analysis["home_advice"]
    
    detected_location = _detect_location(payload.message)
    
    # 2. Query MongoDB for matching doctors
    spec_filters = [
        {"specialization": {"$regex": re.escape(s), "$options": "i"}}
        for s in specializations
    ]
    mongo_query: dict = {"$or": spec_filters} if spec_filters else {}
    if detected_location:
        mongo_query["location"] = {"$regex": re.escape(detected_location), "$options": "i"}
        
    cursor = db.doctors.find(mongo_query).limit(10)
    raw_docs = await cursor.to_list(length=10)
    
    # Fallback: try dropping location if no doctors found
    if not raw_docs and detected_location:
        mongo_query.pop("location", None)
        cursor = db.doctors.find(mongo_query).limit(10)
        raw_docs = await cursor.to_list(length=10)
        
    # Fallback: still no doctors → find any available doctors
    if not raw_docs:
        cursor = db.doctors.find({"is_available": True}).limit(10)
        raw_docs = await cursor.to_list(length=10)
        
    # 3. Score and sort doctors
    scored = sorted(
        [(_score_doctor(d, specializations, detected_location), d) for d in raw_docs],
        key=lambda x: x[0],
        reverse=True,
    )
    
    doctors = [_doc_to_response(doc, score) for score, doc in scored[:3]]
    
    # 4. Formulate empathetic response
    spec_str = " or ".join(specializations)
    
    # Generate triage response
    ai_response = None
    llm = recommender._get_llm()
    if llm:
        prompt = f"""You are a helpful Pakistani AI Medical Triage receptionist at Smart Doctor Connect.
The patient {payload.patient_name} describes their symptoms: "{payload.message}"
Our clinical rules determined:
- Urgency: {urgency.value}
- Specialization: {spec_str}
- Advice: {home_advice}
- City Detected: {detected_location or 'Not specified'}

Write a friendly, professional 2-3 sentence triage message.
Acknowledge their symptoms warmly, explain why you recommend a {spec_str}, and state your home advice.
Keep it concise, reassuring, and clear.
Do NOT write any JSON or markdown formatting, write plain text only."""
        try:
            from langchain_core.messages import HumanMessage
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            ai_response = response.content.strip()
        except Exception:
            pass
            
    if not ai_response:
        # Fallback template
        location_clause = f" in {detected_location}" if detected_location else ""
        doctor_clause = f" I found {len(doctors)} doctor(s){location_clause} who can help you!" if doctors else " I'm checking for available specialists now."
        ai_response = (
            f"Hello {payload.patient_name}, I understand you're experiencing symptoms. "
            f"Based on what you described, I highly recommend consulting a {spec_str}. "
            f"This has been assessed as a {urgency.value} urgency level. "
            f"{home_advice}{doctor_clause}"
        )
        
    return TriageMessageResponse(
        ai_response=ai_response,
        specializations=specializations,
        urgency=urgency,
        home_advice=home_advice,
        doctors=doctors,
    )
