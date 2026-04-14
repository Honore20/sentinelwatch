from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


# --- Paramètres de détection (facilement ajustables) ---
THRESHOLD_COUNT = 5       # Nombre d'échecs pour déclencher une alerte
THRESHOLD_WINDOW = 60     # Fenêtre de temps en secondes


class BruteForceCorrelator:
    """
    Moteur de corrélation : détecte les attaques SSH brute-force.
    
    Règle : si une IP génère >= THRESHOLD_COUNT échecs SSH
    dans une fenêtre de THRESHOLD_WINDOW secondes → ALERTE.
    """

    def __init__(self):
        # Dictionnaire : IP → liste des timestamps d'échecs
        self._failures: dict[str, list[datetime]] = defaultdict(list)

    def add_event(self, source_ip: str, timestamp: datetime) -> Optional[dict]:
        """
        Enregistre un échec SSH et vérifie si le seuil est atteint.
        Retourne un dict d'alerte si brute-force détecté, None sinon.
        """
        now = timestamp
        window_start = now - timedelta(seconds=THRESHOLD_WINDOW)

        # Nettoyage : on garde uniquement les événements dans la fenêtre
        self._failures[source_ip] = [
            t for t in self._failures[source_ip]
            if t >= window_start
        ]

        # Ajout du nouvel échec
        self._failures[source_ip].append(now)
        count = len(self._failures[source_ip])

        # Déclenchement de l'alerte si seuil atteint exactement
        # (on n'alerte qu'une fois par seuil, pas à chaque tentative)
        if count == THRESHOLD_COUNT:
            severity = self._compute_severity(count)
            return {
                "source_ip": source_ip,
                "attempt_count": count,
                "window_seconds": THRESHOLD_WINDOW,
                "severity": severity,
            }

        return None

    def _compute_severity(self, count: int) -> str:
        """Calcule la sévérité de l'alerte selon le nombre de tentatives."""
        if count >= 20:
            return "CRITICAL"
        elif count >= 10:
            return "HIGH"
        elif count >= 5:
            return "MEDIUM"
        return "LOW"
