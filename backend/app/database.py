from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings

settings = get_settings()
database_url = settings.database_url

# Détection du type de DB
is_sqlite = database_url.startswith("sqlite")
is_render_postgres = "render.com" in database_url

# SSL obligatoire pour Render PostgreSQL externe
if is_render_postgres and "sslmode" not in database_url:
    database_url += "?sslmode=require"

# Configuration du moteur selon le type de DB
if is_sqlite:
    # SQLite : args spécifiques + pas de pool
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL : pool de connexions classique
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,   # Recycle les connexions toutes les 5 min (évite timeouts)
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
