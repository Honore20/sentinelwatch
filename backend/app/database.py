from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Création du moteur SQLAlchemy
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # Vérifie la connexion avant chaque requête
    pool_size=10,            # Connexions simultanées max
    max_overflow=20,
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
