from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

connect_args = {}
if "render.com" in settings.database_url:
    connect_args = {"sslmode": "require"}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)
# Factory de sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def get_db():
    """
    Dépendance FastAPI : fournit une session BDD par requête,
    et garantit sa fermeture même en cas d'erreur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
