import asyncio
import logging
import os
from worker.parser import parse_log_line
from worker.correlator import BruteForceCorrelator
from worker.notifier import send_event, send_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sentinel.worker")

LOG_FILE = os.getenv("LOG_FILE", "/logs/auth.log.sample")
POLL_INTERVAL = 2


async def tail_and_process():
    """
    Lit le fichier de logs en mode tail réel :
    mémorise la position du curseur et ne lit que les nouvelles lignes.
    Ainsi, chaque ligne n'est traitée qu'UNE seule fois.
    """
    correlator = BruteForceCorrelator()
    logger.info(f"🚀 SentinelWatch Worker démarré — surveillance de {LOG_FILE}")

    # On attend que le fichier existe
    while not os.path.exists(LOG_FILE):
        logger.warning(f"En attente du fichier {LOG_FILE}...")
        await asyncio.sleep(3)

    # Positionnement à la FIN du fichier au démarrage
    # (on ne rejoue pas les anciens logs, on surveille les nouveaux)
    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)  # Aller à la fin
        position = f.tell()

    logger.info(f"✅ Fichier trouvé — en attente de nouvelles lignes...")

    while True:
        try:
            current_size = os.path.getsize(LOG_FILE)

            if current_size < position:
                # Le fichier a été rotaté ou vidé → on repart du début
                logger.info("🔄 Rotation du fichier détectée — reset du curseur")
                position = 0

            if current_size > position:
                with open(LOG_FILE, "r") as f:
                    f.seek(position)
                    new_lines = f.readlines()
                    position = f.tell()  # Sauvegarde la nouvelle position

                for line in new_lines:
                    event = parse_log_line(line)
                    if not event:
                        continue

                    logger.info(
                        f"[{event['event_type']}] {event['source_ip']} "
                        f"→ user:{event['username']}"
                    )

                    await send_event(event)

                    if event["event_type"] == "FAILED":
                        alert = correlator.add_event(
                            source_ip=event["source_ip"],
                            timestamp=event["timestamp"],
                        )
                        if alert:
                            await send_alert(alert)

        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(tail_and_process())
