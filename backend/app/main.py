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
    allow_origins=["*"],
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
    Endpoint de test : génère des événements d'attaque fictifs
    """
    db = SessionLocal()
    try:
        events_created = []
        for i in range(attempts):
            event = Event(
                timestamp=datetime.utcnow(),
                source_ip=ip,
                username=f"admin_attempt_{i}",
                event_type="FAILED",
                raw_log=f"Test attack attempt {i+1} from {ip}"
            )
            db.add(event)
            events_created.append(event)
        
        db.commit()
        
        return {
            "status": "created",
            "ip": ip,
            "attempts": attempts,
            "events_created": len(events_created)
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()
