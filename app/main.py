"""
Main Application

Entry point of the AI Voice Sales Agent.

Responsibilities
----------------
1. Create FastAPI application.
2. Register all API routers.
3. Configure application metadata.
4. Run background scheduler for auto-calling Pending leads.
"""

import asyncio
import threading

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.leads import router as leads_router
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.voice import router as voice_router
from app.api.twilio import router as twilio_router
from app.api.calls import calls_router
from app.api.notifications import router as notifications_router


app = FastAPI(
    title="AI Voice Sales Agent",
    description="Production Ready AI Voice Sales Agent Backend",
    version="1.0.0",
)


# ----------------------------
# Register Routers
# ----------------------------

app.include_router(health_router)

app.include_router(leads_router)

app.include_router(chat_router)

app.include_router(conversation_router)

app.include_router(voice_router)

# NEW
app.include_router(twilio_router)

app.include_router(calls_router)

app.include_router(notifications_router)


# ----------------------------
# Startup
# ----------------------------

@app.on_event("startup")
async def startup():

    print("=" * 60)
    print("AI Voice Sales Agent Started")
    print("=" * 60)

    # Start setup in a background thread so it doesn't block startup
    import threading
    from app.core.setup_workflows import run_setup
    threading.Thread(target=run_setup, daemon=True).start()

    # Pre-load heavy ML models in a background thread for faster replies
    def preload_models():
        try:
            print("[STARTUP] Pre-loading ML models in the background...")
            from app.services.stt_service import STTService
            from app.services.knowledge_service import KnowledgeService
            
            # Instantiating the services and accessing properties triggers lazy loading in background
            stt = STTService()
            _ = stt.model
            
            ks = KnowledgeService()
            _ = ks.embedding_model
            print("[STARTUP] ML models pre-loaded successfully!")
        except Exception as e:
            print(f"[STARTUP] Error pre-loading ML models: {e}")

    threading.Thread(target=preload_models, daemon=True).start()


# ----------------------------
# Shutdown
# ----------------------------

@app.on_event("shutdown")
async def shutdown():

    print("=" * 60)
    print("AI Voice Sales Agent Stopped")
    print("=" * 60)


@app.get("/")
def root():

    return {
        "project": "AI Voice Sales Agent",
        "version": "1.0.0",
        "status": "Running",
        "docs": "/docs",
        "health": "/health",
    }