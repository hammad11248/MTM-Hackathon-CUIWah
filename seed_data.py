"""
Smart Doctor Connect AI — Seed Data Script
Populates MongoDB with demo doctors across various specializations in Pakistani cities.
Run: python seed_data.py
"""

import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


DEMO_DOCTORS = [
    {
        "name": "Dr. Sara Ahmed",
        "specialization": "Cardiologist",
        "location": "Lahore",
        "consultation_type": "both",
        "email": "sara.ahmed@example.com",
        "phone": "+92 300 1234567",
        "bio": "15 years experience in interventional cardiology. Specializes in heart failure management and preventive cardiology.",
        "experience_years": 15,
        "consultation_fee": 2000,
        "availability": {
            "Monday": ["09:00", "09:30", "10:00", "10:30", "11:00"],
            "Wednesday": ["14:00", "14:30", "15:00", "15:30"],
            "Friday": ["09:00", "09:30", "10:00"],
        },
        "is_available": True,
        "rating": 4.7,
        "total_reviews": 84,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Usman Ali",
        "specialization": "Orthopedic Surgeon",
        "location": "Islamabad",
        "consultation_type": "in_person",
        "email": "usman.ali@example.com",
        "phone": "+92 301 2345678",
        "bio": "Expert in joint replacement surgery and sports medicine. Fellowship from UK.",
        "experience_years": 12,
        "consultation_fee": 2500,
        "availability": {
            "Tuesday": ["10:00", "10:30", "11:00", "11:30"],
            "Thursday": ["14:00", "14:30", "15:00"],
            "Saturday": ["09:00", "09:30", "10:00"],
        },
        "is_available": True,
        "rating": 4.5,
        "total_reviews": 62,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Ayesha Khan",
        "specialization": "Pediatrician",
        "location": "Karachi",
        "consultation_type": "both",
        "email": "ayesha.khan@example.com",
        "phone": "+92 302 3456789",
        "bio": "Compassionate pediatrician with 10 years of experience. Specializes in neonatal care and childhood vaccinations.",
        "experience_years": 10,
        "consultation_fee": 1500,
        "availability": {
            "Monday": ["09:00", "09:30", "10:00", "10:30"],
            "Tuesday": ["14:00", "14:30", "15:00"],
            "Wednesday": ["09:00", "09:30", "10:00"],
            "Thursday": ["14:00", "14:30"],
            "Saturday": ["10:00", "10:30", "11:00"],
        },
        "is_available": True,
        "rating": 4.9,
        "total_reviews": 120,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Bilal Hussain",
        "specialization": "Neurologist",
        "location": "Rawalpindi",
        "consultation_type": "online",
        "email": "bilal.hussain@example.com",
        "phone": "+92 303 4567890",
        "bio": "Board-certified neurologist specializing in migraine, epilepsy, and stroke management.",
        "experience_years": 18,
        "consultation_fee": 3000,
        "availability": {
            "Monday": ["11:00", "11:30", "12:00"],
            "Wednesday": ["10:00", "10:30", "11:00"],
            "Friday": ["14:00", "14:30", "15:00"],
        },
        "is_available": True,
        "rating": 4.6,
        "total_reviews": 75,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Fatima Zahra",
        "specialization": "Dermatologist",
        "location": "Lahore",
        "consultation_type": "both",
        "email": "fatima.zahra@example.com",
        "phone": "+92 304 5678901",
        "bio": "Expert in cosmetic dermatology, acne treatment, and skin allergy management. 8 years experience.",
        "experience_years": 8,
        "consultation_fee": 1800,
        "availability": {
            "Tuesday": ["09:00", "09:30", "10:00", "10:30", "11:00"],
            "Thursday": ["09:00", "09:30", "10:00"],
            "Saturday": ["14:00", "14:30", "15:00"],
        },
        "is_available": True,
        "rating": 4.8,
        "total_reviews": 95,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Hassan Raza",
        "specialization": "General Physician",
        "location": "Faisalabad",
        "consultation_type": "both",
        "email": "hassan.raza@example.com",
        "phone": "+92 305 6789012",
        "bio": "Experienced family physician providing comprehensive primary care. Specializes in diabetes and hypertension management.",
        "experience_years": 20,
        "consultation_fee": 1000,
        "availability": {
            "Monday": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"],
            "Tuesday": ["09:00", "09:30", "10:00", "10:30"],
            "Wednesday": ["14:00", "14:30", "15:00", "15:30"],
            "Thursday": ["09:00", "09:30", "10:00"],
            "Friday": ["09:00", "09:30", "10:00"],
            "Saturday": ["09:00", "09:30"],
        },
        "is_available": True,
        "rating": 4.3,
        "total_reviews": 200,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Zainab Malik",
        "specialization": "Gynecologist",
        "location": "Karachi",
        "consultation_type": "in_person",
        "email": "zainab.malik@example.com",
        "phone": "+92 306 7890123",
        "bio": "Leading gynecologist with expertise in high-risk pregnancies and laparoscopic surgery.",
        "experience_years": 14,
        "consultation_fee": 2200,
        "availability": {
            "Monday": ["10:00", "10:30", "11:00"],
            "Wednesday": ["10:00", "10:30", "11:00"],
            "Friday": ["14:00", "14:30", "15:00"],
        },
        "is_available": True,
        "rating": 4.7,
        "total_reviews": 88,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Ahmed Qureshi",
        "specialization": "Gastroenterologist",
        "location": "Multan",
        "consultation_type": "both",
        "email": "ahmed.qureshi@example.com",
        "phone": "+92 307 8901234",
        "bio": "Specialist in digestive disorders, endoscopy, and liver diseases. 11 years experience.",
        "experience_years": 11,
        "consultation_fee": 1800,
        "availability": {
            "Tuesday": ["09:00", "09:30", "10:00"],
            "Thursday": ["14:00", "14:30", "15:00"],
            "Saturday": ["09:00", "09:30", "10:00", "10:30"],
        },
        "is_available": True,
        "rating": 4.4,
        "total_reviews": 55,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Mariam Siddiqui",
        "specialization": "Psychiatrist",
        "location": "Islamabad",
        "consultation_type": "online",
        "email": "mariam.siddiqui@example.com",
        "phone": "+92 308 9012345",
        "bio": "Compassionate psychiatrist specializing in anxiety, depression, and trauma therapy. Offers online sessions.",
        "experience_years": 9,
        "consultation_fee": 2500,
        "availability": {
            "Monday": ["14:00", "14:30", "15:00", "15:30"],
            "Wednesday": ["14:00", "14:30", "15:00"],
            "Friday": ["10:00", "10:30", "11:00"],
        },
        "is_available": True,
        "rating": 4.8,
        "total_reviews": 67,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Tariq Mehmood",
        "specialization": "ENT Specialist",
        "location": "Peshawar",
        "consultation_type": "in_person",
        "email": "tariq.mehmood@example.com",
        "phone": "+92 309 0123456",
        "bio": "Senior ENT surgeon with 22 years of experience in sinus surgery and hearing restoration.",
        "experience_years": 22,
        "consultation_fee": 1500,
        "availability": {
            "Monday": ["09:00", "09:30", "10:00"],
            "Tuesday": ["09:00", "09:30", "10:00"],
            "Wednesday": ["14:00", "14:30"],
            "Thursday": ["09:00", "09:30"],
        },
        "is_available": True,
        "rating": 4.2,
        "total_reviews": 110,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Nadia Farooq",
        "specialization": "Endocrinologist",
        "location": "Lahore",
        "consultation_type": "both",
        "email": "nadia.farooq@example.com",
        "phone": "+92 310 1234567",
        "bio": "Diabetes and thyroid specialist with advanced training in hormonal disorders.",
        "experience_years": 13,
        "consultation_fee": 2000,
        "availability": {
            "Tuesday": ["10:00", "10:30", "11:00", "11:30"],
            "Thursday": ["10:00", "10:30", "11:00"],
            "Saturday": ["09:00", "09:30"],
        },
        "is_available": True,
        "rating": 4.6,
        "total_reviews": 72,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "name": "Dr. Kamran Shah",
        "specialization": "Pulmonologist",
        "location": "Rawalpindi",
        "consultation_type": "both",
        "email": "kamran.shah@example.com",
        "phone": "+92 311 2345678",
        "bio": "Chest and lung specialist. Expert in asthma, COPD, and tuberculosis management.",
        "experience_years": 16,
        "consultation_fee": 1800,
        "availability": {
            "Monday": ["10:00", "10:30", "11:00"],
            "Wednesday": ["09:00", "09:30", "10:00"],
            "Friday": ["14:00", "14:30", "15:00", "15:30"],
        },
        "is_available": False,
        "rating": 4.1,
        "total_reviews": 48,
        "created_at": datetime.now(timezone.utc),
    },
]


async def seed():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(uri)
    db = client.get_default_database(default="smart_doctor_db")

    # Clear existing doctors to avoid duplicates
    existing = await db.doctors.count_documents({})
    if existing > 0:
        print(f"⚠️  Found {existing} existing doctors. Clearing collection...")
        await db.doctors.delete_many({})

    # Insert demo data
    result = await db.doctors.insert_many(DEMO_DOCTORS)
    print(f"✅ Successfully seeded {len(result.inserted_ids)} demo doctors!")

    # Print summary
    print("\n📋 Seeded Doctors:")
    print(f"{'Name':<25} {'Specialization':<25} {'Location':<15} {'Available'}")
    print("-" * 80)
    for doc in DEMO_DOCTORS:
        status = "✅" if doc["is_available"] else "❌"
        print(f"{doc['name']:<25} {doc['specialization']:<25} {doc['location']:<15} {status}")

    # Create indexes
    await db.doctors.create_index([("name", "text"), ("specialization", "text"), ("bio", "text")])
    await db.doctors.create_index("email", unique=True)
    await db.doctors.create_index("specialization")
    await db.doctors.create_index("location")
    await db.doctors.create_index("is_available")
    print("\n📇 Database indexes created.")

    client.close()
    print("\n🎉 Seed complete! Run the server with: uvicorn api.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(seed())
