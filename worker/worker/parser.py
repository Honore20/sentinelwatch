import re
from datetime import datetime
from typing import Optional


# Patterns regex pour parser les lignes SSH d'auth.log
PATTERNS = {
    "FAILED": re.compile(
        r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)"
        r".*sshd\[\d+\]:\s+Failed password for (?:invalid user )?(?P<username>\S+)"
        r" from (?P<ip>[\d.]+) port \d+"
    ),
    "SUCCESS": re.compile(
        r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)"
        r".*sshd\[\d+\]:\s+Accepted (?:password|publickey) for (?P<username>\S+)"
        r" from (?P<ip>[\d.]+) port \d+"
    ),
}

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_log_line(line: str) -> Optional[dict]:
    """
    Parse une ligne d'auth.log et retourne un dict structuré,
    ou None si la ligne ne correspond à aucun pattern connu.
    """
    line = line.strip()
    if not line:
        return None

    for event_type, pattern in PATTERNS.items():
        match = pattern.search(line)
        if match:
            data = match.groupdict()
            try:
                # Reconstruction de la date (on suppose l'année courante)
                year = datetime.now().year
                month = MONTH_MAP.get(data["month"], 1)
                day = int(data["day"])
                h, m, s = map(int, data["time"].split(":"))
                timestamp = datetime(year, month, day, h, m, s)
            except (ValueError, KeyError):
                timestamp = datetime.now()

            return {
                "event_type": event_type,
                "source_ip": data["ip"],
                "username": data.get("username", "unknown"),
                "timestamp": timestamp,
                "raw_log": line,
            }

    return None  # Ligne ignorée (pas SSH ou pas intéressante)
