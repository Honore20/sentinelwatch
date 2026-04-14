# 🛡️ SentinelWatch

> Mini-SOC automatisé — Détection et réponse aux attaques SSH brute-force en temps réel

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Security](https://img.shields.io/badge/Security-JWT%20%7C%20bcrypt-red?logo=shield)

---

## 🎯 Présentation

**SentinelWatch** est une plateforme de supervision sécurité (SOC) légère, construite de A à Z, qui :

- **Analyse en temps réel** les logs d'authentification SSH (`auth.log`)
- **Détecte automatiquement** les attaques par brute-force grâce à des règles de corrélation (X échecs en Y secondes)
- **Déclenche une réponse active** : bannissement automatique de l'IP attaquante
- **Affiche tout en direct** sur un dashboard SOC via WebSocket

Ce projet démontre une maîtrise concrète des concepts SOC/SIEM, de l'architecture backend sécurisée et des bonnes pratiques DevSecOps.

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Worker  │───▶│  FastAPI API │───▶│  PostgreSQL   │  │
│  │(log tail)│    │  (port 8000) │    │  (port 5432)  │  │
│  └──────────┘    └──────┬───────┘    └───────────────┘  │
│                         │ WebSocket                      │
│                  ┌──────▼───────┐                        │
│                  │   Frontend   │                        │
│                  │  Dashboard   │                        │
│                  │  (port 3000) │                        │
│                  └──────────────┘                        │
└─────────────────────────────────────────────────────────┘

### Flux de détection
auth.log → Worker (tail) → Parser (regex) → Correlator → Alerte
│
API FastAPI
/     │      
Events   Alerts   BannedIPs
\     │      /
PostgreSQL BDD
│
WebSocket broadcast
│
Dashboard temps réel

---

## 🔧 Stack Technique

| Composant | Technologie | Justification |
|---|---|---|
| **Backend** | FastAPI (Python 3.12) | Async natif, doc Swagger auto, haute performance |
| **Worker** | Python asyncio + watchdog | Lecture incrémentale des logs (tail réel) |
| **Base de données** | PostgreSQL 16 | Robustesse, requêtes complexes, standard industrie |
| **Auth** | JWT + bcrypt | Standard sécurité industrie |
| **Frontend** | HTML + Tailwind + Alpine.js | Léger, pas de framework lourd, focus sur la cyber |
| **Temps réel** | WebSocket | Push serveur → client sans polling |
| **Infra** | Docker Compose | Reproductible, isolé, déployable en 1 commande |

---

## 🚀 Lancement rapide

### Prérequis
- Docker Desktop ≥ 24
- Docker Compose ≥ 2
- Python 3.11+

### 1. Clone et configuration

```bash
git clone https://github.com/Honore20/sentinelwatch.git
cd sentinelwatch

# Copier et adapter les variables d'environnement
cp .env.example .env
# ⚠️ Modifier SECRET_KEY et POSTGRES_PASSWORD dans .env !
```

### 2. Lancement

```bash
docker compose up --build -d
```

### 3. Accès

| Service | URL |
|---|---|
| 🖥️ Dashboard SOC | http://localhost:3000 |
| 📡 API REST | http://localhost:8000 |
| 📖 Swagger UI | http://localhost:8000/docs |

### 4. Créer un compte analyste

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"analyste","email":"analyste@soc.fr","password":"MonMotDePasse123!"}'
```

---

## 🎬 Démo — Simuler une attaque

Ouvre le dashboard sur http://localhost:3000, puis dans un autre terminal :

```bash
# Attaque brute-force classique (déclenche une alerte en ~5s)
python3 tools/attack_simulator.py --ip 10.10.10.10 --count 7 --delay 1

# Vague multi-sources (plusieurs IPs simultanées)
python3 tools/attack_simulator.py --scenario wave

# Attaque furtive (sous le seuil de détection)
python3 tools/attack_simulator.py --scenario stealth
```

**Ce que tu observes en direct sur le dashboard :**
1. Les événements `FAILED` s'accumulent dans le flux
2. Au 5ème échec en moins de 60s → alerte rouge `MEDIUM`
3. L'IP est bannie automatiquement dans le tableau

---

## 🔐 Sécurité — Concepts démontrés

| Concept | Implémentation |
|---|---|
| **Détection d'intrusion (IDS)** | Règles de corrélation SSH brute-force |
| **Réponse à incident (IPS)** | Bannissement automatique de l'IP |
| **SIEM (simplifié)** | Centralisation, parsing et corrélation des logs |
| **Authentification sécurisée** | JWT HS256 + hashing bcrypt |
| **Principe du moindre privilège** | Endpoints internes séparés des endpoints publics |
| **Journalisation** | Logs structurés sur tous les services |
| **Isolation** | Chaque service dans son propre conteneur Docker |

---

## 📊 Analyse de Risque EBIOS RM (extrait)

> Appliquée au scénario : **"Compromission d'un serveur Linux via SSH"**

**Atelier 1 — Socle de sécurité**
- Bien support : Serveur Linux exposant SSH (port 22)
- Valeur métier : Disponibilité et intégrité du serveur

**Atelier 2 — Sources de risque**
- SR1 : Attaquant externe opportuniste (script-kiddie, botnet)
- SR2 : Attaquant ciblé (APT)

**Atelier 3 — Scénarios stratégiques**
- Scénario : Compromission des credentials SSH → accès root → persistance

**Atelier 4 — Scénarios opérationnels**
- Vecteur : Brute-force SSH (Hydra, Medusa)
- Détection : Règle de corrélation (5 échecs / 60s) → alerte SOC
- Réponse : Bannissement IP automatique + notification analyste

**Atelier 5 — Traitement du risque**
- Mesure 1 : Désactiver l'auth par mot de passe (clés SSH uniquement)
- Mesure 2 : Fail2ban / SentinelWatch pour détection automatique
- Mesure 3 : Supervision SOC 24/7 avec escalade

---

## 📁 Structure du projet
sentinelwatch/
├── backend/          # API FastAPI (auth, events, alertes, WebSocket)
├── worker/           # Collecteur de logs (tail, parser, correlator)
├── frontend/         # Dashboard SOC (HTML + Tailwind + Alpine.js)
├── tools/            # Scripts utilitaires (simulateur d'attaques)
├── docs/             # Documentation architecture & EBIOS RM
└── docker-compose.yml

---

## 👨‍💻 Auteur

**Honoré Avekor**
Bachelor SIN2 — EPSI Toulouse
Alternance Cybersécurité & Infrastructure (12 mois)

[![GitHub](https://img.shields.io/badge/GitHub-Honore20-black?logo=github)](https://github.com/Honore20)
