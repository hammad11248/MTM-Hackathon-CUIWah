"""
Smart Doctor Connect AI — Email Service
Simulates email notifications and logs them to MongoDB.
In production, swap the print statements with SendGrid / SMTP calls.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from api.database import get_db

logger = logging.getLogger(__name__)


async def send_doctor_notification(
    doctor_email: str,
    doctor_name: str,
    patient_name: str,
    patient_contact: Optional[str],
    message: str,
) -> bool:
    """
    Notify a doctor about a new patient message.
    Logs the email to MongoDB and prints to console (simulated).
    """
    db = await get_db()

    email_record = {
        "type": "doctor_notification",
        "to": doctor_email,
        "subject": f"New Patient Message — {patient_name}",
        "body": (
            f"Dear {doctor_name},\n\n"
            f"You have a new message from {patient_name}"
            f"{f' (Contact: {patient_contact})' if patient_contact else ''}.\n\n"
            f'Message: "{message}"\n\n'
            f"Please log in to Smart Doctor Connect to respond.\n\n"
            f"— Smart Doctor Connect AI"
        ),
        "sent_at": datetime.now(timezone.utc),
        "status": "simulated",
    }

    try:
        await db.email_logs.insert_one(email_record)
        # Simulated email send — replace with real SMTP/SendGrid in production
        logger.info(
            f"📧 EMAIL SENT (simulated)\n"
            f"   To: {doctor_email}\n"
            f"   Subject: New Patient Message — {patient_name}\n"
            f"   Patient Contact: {patient_contact or 'N/A'}\n"
            f"   Message: {message[:100]}..."
        )
        print(
            f"\n{'='*60}\n"
            f"📧 EMAIL NOTIFICATION (Simulated)\n"
            f"{'='*60}\n"
            f"To: {doctor_email}\n"
            f"Subject: New Patient Message — {patient_name}\n"
            f"Patient Contact: {patient_contact or 'N/A'}\n"
            f"Message: {message}\n"
            f"{'='*60}\n"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log email notification: {e}")
        return False


async def send_appointment_confirmation(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    date: str,
    time_slot: str,
    consultation_type: str,
    queue_position: int,
    predicted_wait: Optional[int] = None,
) -> bool:
    """
    Send appointment confirmation email to the patient.
    Logs to MongoDB and prints to console (simulated).
    """
    db = await get_db()

    wait_info = f"Estimated wait: ~{predicted_wait} minutes" if predicted_wait else "You are next in queue"

    email_record = {
        "type": "appointment_confirmation",
        "to": patient_email,
        "subject": f"Appointment Confirmed — {doctor_name}",
        "body": (
            f"Dear {patient_name},\n\n"
            f"Your appointment has been confirmed!\n\n"
            f"Doctor: {doctor_name}\n"
            f"Date: {date}\n"
            f"Time: {time_slot}\n"
            f"Type: {consultation_type}\n"
            f"Queue Position: #{queue_position}\n"
            f"{wait_info}\n\n"
            f"Please arrive 10 minutes early for in-person visits.\n\n"
            f"— Smart Doctor Connect AI"
        ),
        "sent_at": datetime.now(timezone.utc),
        "status": "simulated",
    }

    try:
        await db.email_logs.insert_one(email_record)
        print(
            f"\n{'='*60}\n"
            f"📧 APPOINTMENT CONFIRMATION (Simulated)\n"
            f"{'='*60}\n"
            f"To: {patient_email}\n"
            f"Doctor: {doctor_name}\n"
            f"Date: {date} at {time_slot}\n"
            f"Type: {consultation_type}\n"
            f"Queue Position: #{queue_position}\n"
            f"{'='*60}\n"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log appointment confirmation: {e}")
        return False


async def send_followup_reminder(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    original_message: str,
) -> bool:
    """
    Send a follow-up reminder to the patient (scheduled via APScheduler).
    """
    db = await get_db()

    email_record = {
        "type": "followup_reminder",
        "to": patient_email,
        "subject": f"Follow-up Reminder — {doctor_name}",
        "body": (
            f"Dear {patient_name},\n\n"
            f"This is a follow-up regarding your earlier message to {doctor_name}.\n\n"
            f'Your message: "{original_message[:200]}"\n\n'
            f"If you haven't received a response yet, we recommend:\n"
            f"1. Booking an appointment through our platform\n"
            f"2. Trying another available doctor in the same specialty\n"
            f"3. Visiting the nearest hospital if symptoms are urgent\n\n"
            f"— Smart Doctor Connect AI"
        ),
        "sent_at": datetime.now(timezone.utc),
        "status": "simulated",
    }

    try:
        await db.email_logs.insert_one(email_record)
        print(
            f"\n{'='*60}\n"
            f"📧 FOLLOW-UP REMINDER (Simulated)\n"
            f"{'='*60}\n"
            f"To: {patient_email}\n"
            f"Re: Message to {doctor_name}\n"
            f"{'='*60}\n"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send follow-up reminder: {e}")
        return False
