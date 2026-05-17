"""
Smart Doctor Connect AI — MongoDB Connection Manager
Uses Motor (async) driver. Indexes are created on startup.

On Vercel serverless, the lifespan event may not fire reliably for
every cold-start invocation. This module therefore uses a lazy-connect
pattern: get_db() will auto-connect on first call if needed.
"""

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None
_indexes_created: bool = False


async def connect_db() -> None:
    global _client, _db, _indexes_created

    if _client is not None:
        return  # already connected

    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    _client = AsyncIOMotorClient(uri)
    _db = _client.get_default_database(default="smart_doctor_db")

    # ── Indexes ────────────────────────────────────────────────────────────────
    if not _indexes_created:
        try:
            # Doctors: text search + unique email
            await _db.doctors.create_index([("name", "text"), ("specialization", "text"), ("bio", "text")])
            await _db.doctors.create_index("email", unique=True)
            await _db.doctors.create_index("specialization")
            await _db.doctors.create_index("location")
            await _db.doctors.create_index("is_available")

            # Appointments: prevent double-booking + fast lookup
            await _db.appointments.create_index(
                [("doctor_id", 1), ("date", 1), ("time_slot", 1)], unique=True
            )
            await _db.appointments.create_index("doctor_id")
            await _db.appointments.create_index("patient_email")

            # Messages
            await _db.messages.create_index("doctor_id")
            await _db.messages.create_index("created_at")

            _indexes_created = True
        except Exception as e:
            print(f"Index creation warning (may already exist): {e}")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()


async def get_db() -> AsyncIOMotorDatabase:
    """
    Returns the database instance, auto-connecting on first call.
    This handles Vercel serverless cold starts where lifespan may not fire.
    """
    global _db
    if _db is None:
        await connect_db()
    return _db
