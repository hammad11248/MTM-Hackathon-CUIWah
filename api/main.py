"""
Smart Doctor Connect AI — FastAPI Entry Point
Handles app lifecycle, CORS, rate limiting, and router registration.
"""

import os
import sys
from contextlib import asynccontextmanager

# ─────────────────────────────────────────────────────────────
# Path Configuration for Direct Execution
# ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from api.database import connect_db, close_db
from api.limiter import limiter
from api.services.scheduler import scheduler
from api.routers import doctors, appointments, chat, agents

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

    try:
        await connect_db()
        print("Database connected successfully.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("The app will continue running, but database features will be unavailable.")

    # APScheduler is only supported in long-running processes (not Vercel serverless)
    if ENVIRONMENT == "development":
        if not scheduler.running:
            scheduler.start()

    yield

    print("Closing application...")

    await close_db()

    if ENVIRONMENT == "development" and scheduler.running:
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

app.include_router(
    agents.router,
    prefix="/api",
    tags=["Agents"]
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

# ─────────────────────────────────────────────────────────────
# Static Files
# On Vercel, static files are served by @vercel/static via routes.
# In development, FastAPI serves them directly.
# ─────────────────────────────────────────────────────────────
if ENVIRONMENT == "development":
    import os as _os
    _public_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "public")
    if _os.path.isdir(_public_dir):
        app.mount("/", StaticFiles(directory=_public_dir, html=True), name="static")

# ─────────────────────────────────────────────────────────────
# Direct Execution Support
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)