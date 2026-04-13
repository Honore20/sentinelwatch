from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.database import Base


class Alert(Base):
    """
    Alerte générée quand une IP dépasse le seuil de tentatives.
    Ex: 5 échecs SSH en moins de 60 secondes → brute-force détecté.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    source_ip = Column(String(45), nullable=False, index=True)
    attempt_count = Column(Integer, nullable=False)    # Nb tentatives détectées
    window_seconds = Column(Integer, nullable=False)   # Fenêtre de temps (ex: 60s)
    severity = Column(String(20), default="HIGH")      # LOW / MEDIUM / HIGH / CRITICAL
    acknowledged = Column(Boolean, default=False)      # L'analyste a-t-il traité l'alerte ?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
