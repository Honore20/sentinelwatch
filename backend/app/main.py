from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.config import get_settings
from app.routers import auth, events, websocket
from app.models.event import Event
from datetime import datetime

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SentinelWatch API",
    description="Mini-SOC : détection et réponse aux attaques SSH brute-force",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo : on autorise tout. En prod : restreindre.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(websocket.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "project": "SentinelWatch", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "environment": settings.environment}

@app.post("/api/test-attack", tags=["Testing"])
def test_attack(ip: str = "203.45.67.89", attempts: int = 5):
    """
    Endpoint de test : génère un événement d'attaque fictif
    Utile pour tester le dashboard en live
    """
    db = SessionLocal()
    try:
        event = Event(
            event_type="ssh_bruteforce",
            source_ip=ip,
            port=22,
            protocol="SSH",
            description=f"Test attack: {attempts} failed login attempts from {ip}",
            severity="CRITICAL" if attempts > 5 else "HIGH",
            timestamp=datetime.utcnow(),
            metadata={"attempts": attempts, "test": True}
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return {
            "status": "created",
            "event_id": event.id,
            "ip": ip,
            "attempts": attempts,
            "severity": event.severity
        }
    finally:
        db.close()
