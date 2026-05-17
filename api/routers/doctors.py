"""
Smart Doctor Connect AI — Doctors Router
Endpoints: register, fetch, update, AI-powered search.
The search pipeline: raw text → LLM/rule-based specialization → MongoDB query → scoring.
"""

from __future__ import annotations

import re
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.database import get_db
from api.limiter import limiter
from api.models import (
    AISearchResult,
    DoctorCreate,
    DoctorInDB,
    DoctorResponse,
    DoctorUpdate,
    UrgencyLevel,
)
from api.services.recommender import SymptomRecommender

router = APIRouter()
recommender = SymptomRecommender()   # singleton

# ── Pakistani cities for location detection ───────────────────────────────────
PAKISTAN_CITIES = {
    "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "multan",
    "peshawar", "quetta", "sialkot", "gujranwala", "hyderabad", "abbottabad",
    "wah", "taxila", "attock", "murree", "bahawalpur", "sargodha",
}


def _detect_location(text: str) -> Optional[str]:
    """Extract the first Pakistani city name from free text."""
    lower = text.lower()
    for city in PAKISTAN_CITIES:
        if city in lower:
            return city.title()
    return None


def _score_doctor(doc: dict, specializations: List[str], location: Optional[str]) -> int:
    """
    Compute a 0-100 match score.
    Weights: specialization 50 | location 30 | availability 10 | rating 10
    """
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
    score += min(10, int(rating * 2))  # 5-star → 10 pts

    return min(score, 100)


def _doc_to_response(doc: dict, match_score: Optional[int] = None) -> DoctorResponse:
    doc["_id"] = str(doc["_id"])
    return DoctorResponse(**doc, match_score=match_score)


# ── Register Doctor ───────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=DoctorInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor",
)
async def register_doctor(payload: DoctorCreate):
    db = await get_db()

    # Prevent duplicate email registrations
    existing = await db.doctors.find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A doctor with this email already exists.",
        )

    doc_dict = payload.model_dump()
    result = await db.doctors.insert_one(doc_dict)
    created = await db.doctors.find_one({"_id": result.inserted_id})
    return _doc_to_response(created)


# ── AI-Powered Doctor Search ──────────────────────────────────────────────────
@router.get(
    "/search",
    response_model=AISearchResult,
    summary="AI symptom-to-doctor search",
)
@limiter.limit("30/minute")
async def search_doctors(
    request: Request,
    q: str = Query(..., min_length=3, max_length=500, description="Patient symptoms or free-text query"),
    limit: int = Query(default=6, ge=1, le=20),
):
    db = await get_db()

    # ── Step 1: Analyse symptoms ──────────────────────────────────────────────
    analysis = await recommender.analyse(q)          # always returns a result
    specializations: List[str] = analysis["specializations"]
    urgency: UrgencyLevel = UrgencyLevel(analysis["urgency"].upper())
    home_advice: str = analysis["home_advice"]
    detected_location = _detect_location(q)

    # ── Step 2: Build MongoDB query ───────────────────────────────────────────
    # Use $or to match any of the recommended specializations (case-insensitive)
    spec_filters = [
        {"specialization": {"$regex": re.escape(s), "$options": "i"}}
        for s in specializations
    ]
    mongo_query: dict = {"$or": spec_filters} if spec_filters else {}

    if detected_location:
        mongo_query["location"] = {"$regex": re.escape(detected_location), "$options": "i"}

    # Fetch a wider pool so scoring can pick the best matches
    cursor = db.doctors.find(mongo_query).limit(limit * 3)
    raw_docs = await cursor.to_list(length=limit * 3)

    # Fallback: no location-restricted results → drop location filter
    if not raw_docs and detected_location:
        mongo_query.pop("location", None)
        cursor = db.doctors.find(mongo_query).limit(limit * 3)
        raw_docs = await cursor.to_list(length=limit * 3)

    # Fallback: still nothing → return available doctors of any specialization
    if not raw_docs:
        cursor = db.doctors.find({"is_available": True}).limit(limit * 3)
        raw_docs = await cursor.to_list(length=limit * 3)

    # ── Step 3: Score & rank ──────────────────────────────────────────────────
    scored = sorted(
        [(_score_doctor(d, specializations, detected_location), d) for d in raw_docs],
        key=lambda x: x[0],
        reverse=True,
    )

    doctors = [_doc_to_response(doc, score) for score, doc in scored[:limit]]

    return AISearchResult(
        specializations=specializations,
        urgency=urgency,
        home_advice=home_advice,
        detected_location=detected_location,
        doctors=doctors,
    )


# ── Get Doctor by ID ──────────────────────────────────────────────────────────
@router.get("/{doctor_id}", response_model=DoctorResponse, summary="Fetch a doctor profile")
async def get_doctor(doctor_id: str):
    db = await get_db()
    try:
        oid = ObjectId(doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    doc = await db.doctors.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return _doc_to_response(doc)


# ── Update Doctor ─────────────────────────────────────────────────────────────
@router.put("/{doctor_id}", response_model=DoctorResponse, summary="Update doctor profile")
async def update_doctor(doctor_id: str, payload: DoctorUpdate):
    db = await get_db()
    try:
        oid = ObjectId(doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor ID format.")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    result = await db.doctors.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    updated = await db.doctors.find_one({"_id": oid})
    return _doc_to_response(updated)


# ── List All Doctors (paginated) ──────────────────────────────────────────────
@router.get("/", response_model=List[DoctorResponse], summary="List all doctors")
async def list_doctors(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    db = await get_db()
    cursor = db.doctors.find().skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_doc_to_response(d) for d in docs]
