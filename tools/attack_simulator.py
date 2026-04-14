#!/usr/bin/env python3
"""
SentinelWatch — Attack Simulator
=================================
Simule des attaques SSH brute-force en injectant des lignes
dans le fichier de logs surveillé par le Worker.

Usage:
    python3 tools/attack_simulator.py --ip 10.0.0.99 --count 10 --delay 0.5
    python3 tools/attack_simulator.py --scenario wave   # Vague d'attaques
    python3 tools/attack_simulator.py --scenario stealth # Attaque lente discrète

Parfait pour démontrer SentinelWatch en entretien !
"""

import argparse
import time
import os
import random
from datetime import datetime

# Chemin vers le fichier de logs (relatif à la racine du projet)
LOG_FILE = os.path.join(
    os.path.dirname(__file__),
    "../worker/sample_logs/auth.log.sample"
)

# Usernames typiques tentés lors d'un brute-force SSH réel
COMMON_USERNAMES = [
    "root", "admin", "ubuntu", "user", "test",
    "deploy", "git", "postgres", "mysql", "oracle",
    "administrator", "guest", "pi", "hadoop", "ftpuser"
]

HOSTNAME = "sentinelwatch-server"


def make_failed_line(ip: str, username: str) -> str:
    """Génère une ligne auth.log réaliste pour un échec SSH."""
    now = datetime.now()
    month = now.strftime("%b")
    day = now.strftime("%d").lstrip("0") or "1"
    t = now.strftime("%H:%M:%S")
    pid = random.randint(10000, 99999)
    port = random.randint(1024, 65535)
    return (
        f"{month} {day} {t} {HOSTNAME} sshd[{pid}]: "
        f"Failed password for {username} from {ip} port {port} ssh2\n"
    )


def make_success_line(ip: str, username: str) -> str:
    """Génère une ligne auth.log réaliste pour une connexion réussie."""
    now = datetime.now()
    month = now.strftime("%b")
    day = now.strftime("%d").lstrip("0") or "1"
    t = now.strftime("%H:%M:%S")
    pid = random.randint(10000, 99999)
    port = random.randint(1024, 65535)
    return (
        f"{month} {day} {t} {HOSTNAME} sshd[{pid}]: "
        f"Accepted password for {username} from {ip} port {port} ssh2\n"
    )


def append_to_log(line: str):
    """Ajoute une ligne au fichier de logs surveillé par le Worker."""
    log_path = os.path.abspath(LOG_FILE)
    with open(log_path, "a") as f:
        f.write(line)


def scenario_brute_force(ip: str, count: int, delay: float):
    """Scénario : attaque brute-force classique depuis une seule IP."""
    print(f"\n🔴 SCÉNARIO : Brute-Force SSH")
    print(f"   IP attaquante  : {ip}")
    print(f"   Tentatives     : {count}")
    print(f"   Délai          : {delay}s entre chaque tentative")
    print(f"   Seuil alerte   : 5 tentatives en 60s")
    print(f"\n{'─'*50}")

    for i in range(1, count + 1):
        username = random.choice(COMMON_USERNAMES)
        line = make_failed_line(ip, username)
        append_to_log(line)
        status = "🚨 SEUIL ATTEINT → ALERTE!" if i == 5 else f"   tentative {i}/{count}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILED {ip} → {username} | {status}")
        time.sleep(delay)

    print(f"\n✅ Simulation terminée — vérifie ton dashboard !")


def scenario_wave():
    """Scénario : vague d'attaques depuis plusieurs IPs simultanées."""
    attackers = [
        "45.33.32.156",
        "198.51.100.42",
        "203.0.113.99",
        "91.108.4.200",
    ]
    print(f"\n🌊 SCÉNARIO : Vague multi-sources ({len(attackers)} IPs)")
    print(f"{'─'*50}")

    for round_num in range(1, 4):
        print(f"\n📡 Vague {round_num}/3")
        for ip in attackers:
            username = random.choice(COMMON_USERNAMES)
            line = make_failed_line(ip, username)
            append_to_log(line)
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] FAILED {ip} → {username}")
            time.sleep(0.3)
        time.sleep(2)

    print(f"\n✅ Vague terminée — plusieurs alertes attendues sur le dashboard !")


def scenario_stealth():
    """Scénario : attaque lente (sous les radars du seuil standard)."""
    ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    print(f"\n🥷 SCÉNARIO : Attaque furtive (slow brute-force)")
    print(f"   IP             : {ip}")
    print(f"   Stratégie      : 1 tentative toutes les 15s (sous le seuil)")
    print(f"{'─'*50}")

    for i in range(1, 4):
        username = random.choice(COMMON_USERNAMES)
        line = make_failed_line(ip, username)
        append_to_log(line)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILED {ip} → {username} (tentative {i}/3)")
        if i < 3:
            print(f"   ⏳ Attente 15s (simulation attaque lente)...")
            time.sleep(15)

    print(f"\n💡 Cette IP reste sous le seuil — pas d'alerte générée.")
    print(f"   En vrai SOC : on ajusterait les règles de détection.")


def main():
    parser = argparse.ArgumentParser(
        description="SentinelWatch Attack Simulator — outil de démo"
    )
    parser.add_argument("--ip", default="192.168.100.100",
                        help="IP attaquante (défaut: 192.168.100.100)")
    parser.add_argument("--count", type=int, default=7,
                        help="Nombre de tentatives (défaut: 7)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Délai entre tentatives en secondes (défaut: 1.0)")
    parser.add_argument("--scenario", choices=["brute", "wave", "stealth"],
                        default="brute",
                        help="Scénario : brute / wave / stealth (défaut: brute)")

    args = parser.parse_args()

    print("=" * 50)
    print("  🛡️  SentinelWatch — Attack Simulator")
    print("  Ouvre http://localhost:3000 pour voir le dashboard")
    print("=" * 50)

    if args.scenario == "brute":
        scenario_brute_force(args.ip, args.count, args.delay)
    elif args.scenario == "wave":
        scenario_wave()
    elif args.scenario == "stealth":
        scenario_stealth()


if __name__ == "__main__":
    main()
