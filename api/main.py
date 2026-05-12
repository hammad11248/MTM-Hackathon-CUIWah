"""
Smart Doctor Connect AI — FastAPI Entry Point
Handles app lifecycle, CORS, rate limiting, and router registration.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from api.database import connect_db, close_db
from api.limiter import limiter
from api.services.scheduler import scheduler
from api.routers import doctors, appointments, chat

# ─────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# ─────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting application...")

    await connect_db()

    if not scheduler.running:
        scheduler.start()

    yield

    print("Closing application...")

    await close_db()

    if scheduler.running:
        scheduler.shutdown()


# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Doctor Connect AI",
    description="AI-powered doctor discovery and appointment booking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────
app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────
app.include_router(
    doctors.router,
    prefix="/api/doctors",
    tags=["Doctors"]
)

app.include_router(
    appointments.router,
    prefix="/api/appointments",
    tags=["Appointments"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)

# ─────────────────────────────────────────────────────────────
# Static Files
# ─────────────────────────────────────────────────────────────
if ENVIRONMENT == "development":
    app.mount(
        "/",
        StaticFiles(directory="public", html=True),
        name="static"
    )

# ─────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "environment": ENVIRONMENT
    }