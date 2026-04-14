import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# URL de l'API (via le réseau Docker interne)
API_BASE_URL = "http://api:8000"


async def send_event(event: dict) -> bool:
    """Envoie un événement SSH parsé à l'API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "source_ip": event["source_ip"],
                "username": event["username"],
                "event_type": event["event_type"],
                "timestamp": event["timestamp"].isoformat(),
                "raw_log": event["raw_log"],
            }
            response = await client.post(
                f"{API_BASE_URL}/internal/events",
                json=payload,
            )
            return response.status_code == 201
    except Exception as e:
        logger.error(f"Erreur envoi événement : {e}")
        return False


async def send_alert(alert: dict) -> bool:
    """Envoie une alerte brute-force détectée à l'API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/internal/alerts",
                json=alert,
            )
            if response.status_code == 201:
                logger.warning(
                    f"🚨 ALERTE BRUTE-FORCE : {alert['source_ip']} "
                    f"→ {alert['attempt_count']} tentatives en "
                    f"{alert['window_seconds']}s [Sévérité: {alert['severity']}]"
                )
                return True
    except Exception as e:
        logger.error(f"Erreur envoi alerte : {e}")
    return False
