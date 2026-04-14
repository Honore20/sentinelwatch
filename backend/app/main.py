from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import get_settings
from app.routers import auth, events, websocket

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
