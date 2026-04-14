from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.event import Event
from app.models.alert import Alert
from app.models.banned_ip import BannedIP
from app.routers.websocket import manager
from pydantic import BaseModel

router = APIRouter()


class EventCreate(BaseModel):
    source_ip: str
    username: str
    event_type: str
    timestamp: datetime
    raw_log: str


class AlertCreate(BaseModel):
    source_ip: str
    attempt_count: int
    window_seconds: int
    severity: str


@router.post("/internal/events", status_code=201, tags=["Internal"])
async def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Reçoit un événement SSH parsé depuis le Worker et broadcast aux clients WS."""
    event = Event(
        source_ip=event_data.source_ip,
        username=event_data.username,
        event_type=event_data.event_type,
        timestamp=event_data.timestamp,
        raw_log=event_data.raw_log,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Broadcast temps réel au dashboard
    await manager.broadcast({
        "type": "event",
        "data": {
            "id": event.id,
            "source_ip": event.source_ip,
            "username": event.username,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
        }
    })

    return {"status": "created"}


@router.post("/internal/alerts", status_code=201, tags=["Internal"])
async def create_alert(alert_data: AlertCreate, db: Session = Depends(get_db)):
    """Reçoit une alerte brute-force et bannit l'IP. Broadcast WS."""
    alert = Alert(
        source_ip=alert_data.source_ip,
        attempt_count=alert_data.attempt_count,
        window_seconds=alert_data.window_seconds,
        severity=alert_data.severity,
    )
    db.add(alert)

    existing = db.query(BannedIP).filter(
        BannedIP.ip_address == alert_data.source_ip
    ).first()
    if not existing:
        banned = BannedIP(
            ip_address=alert_data.source_ip,
            reason=f"Brute-force SSH : {alert_data.attempt_count} tentatives détectées",
        )
        db.add(banned)

    db.commit()
    db.refresh(alert)

    # Broadcast de l'alerte au dashboard
    await manager.broadcast({
        "type": "alert",
        "data": {
            "id": alert.id,
            "source_ip": alert.source_ip,
            "attempt_count": alert.attempt_count,
            "window_seconds": alert.window_seconds,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
    })

    return {"status": "alert created", "ip_banned": not bool(existing)}


@router.get("/events", tags=["SOC Dashboard"])
def list_events(limit: int = 50, db: Session = Depends(get_db)):
    """Retourne les derniers événements SSH."""
    events = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
    return events


@router.get("/alerts", tags=["SOC Dashboard"])
def list_alerts(db: Session = Depends(get_db)):
    """Retourne toutes les alertes brute-force."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    return alerts


@router.get("/banned-ips", tags=["SOC Dashboard"])
def list_banned_ips(db: Session = Depends(get_db)):
    """Retourne la liste des IPs bannies."""
    banned = db.query(BannedIP).filter(BannedIP.is_active == True).all()
    return banned


@router.patch("/alerts/{alert_id}/acknowledge", tags=["SOC Dashboard"])
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Marque une alerte comme traitée par l'analyste."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"status": "acknowledged"}


@router.get("/stats", tags=["SOC Dashboard"])
def get_stats(db: Session = Depends(get_db)):
    """Retourne les statistiques pour le dashboard."""
    return {
        "total_events": db.query(Event).count(),
        "failed_events": db.query(Event).filter(Event.event_type == "FAILED").count(),
        "success_events": db.query(Event).filter(Event.event_type == "SUCCESS").count(),
        "total_alerts": db.query(Alert).count(),
        "unack_alerts": db.query(Alert).filter(Alert.acknowledged == False).count(),
        "banned_ips": db.query(BannedIP).filter(BannedIP.is_active == True).count(),
    }
