from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Event(Base):
    """
    Événement SSH parsé depuis auth.log.
    Ex: tentative de connexion échouée depuis une IP.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source_ip = Column(String(45), nullable=False, index=True)  # IPv4 + IPv6
    username = Column(String(100))                               # Utilisateur tenté
    event_type = Column(String(50), nullable=False)             # FAILED / SUCCESS
    raw_log = Column(String(500))                               # Ligne brute du log
    created_at = Column(DateTime(timezone=True), server_default=func.now())
