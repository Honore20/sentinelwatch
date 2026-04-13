from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.database import Base


class BannedIP(Base):
    """IP bloquée automatiquement suite à une alerte brute-force."""
    __tablename__ = "banned_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    reason = Column(String(200))
    banned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = permanent
    is_active = Column(Boolean, default=True)
