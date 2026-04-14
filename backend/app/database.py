from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Render PostgreSQL : on s'assure que sslmode=require est dans l'URL
database_url = settings.database_url
if "render.com" in database_url and "sslmode" not in database_url:
    database_url += "?sslmode=require"

# psycopg2 gère SSL via l'URL — pas via connect_args
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
