from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.config import get_settings
from app.routers import auth, events, websocket
from app.models.event import Event
from app.models.user import User
from datetime import datetime, timedelta
from passlib.context import CryptContext
import random
import os

settings = get_settings()

# Créer le dossier data/ s'il n'existe pas (pour SQLite)
if settings.database_url.startswith("sqlite"):
    os.makedirs("./data", exist_ok=True)

# Création automatique des tables au démarrage
# Compatible PostgreSQL ET SQLite
Base.metadata.create_all(bind=engine)

# Context pour hasher les mots de passe (compatible avec ton auth)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_demo_user():
    """
    Crée automatiquement un compte démo si la table users est vide.
    Permet à n'importe quel recruteur de se connecter directement.
    """
    db = SessionLocal()
    try:
        if not db.query(User).first():
            demo_user = User(
                username="demo",
                email="demo@sentinelwatch.fr",
                hashed_password=pwd_context.hash("DemoSentinel2026!"),
                is_active=True,
                is_admin=False,
            )
            db.add(demo_user)
            db.commit()
            print("✅ Compte démo créé : demo / DemoSentinel2026!")
    except Exception as e:
        print(f"⚠️ Erreur lors de la création du compte démo : {e}")
        db.rollback()
    finally:
        db.close()


# Seed le compte démo au démarrage
seed_demo_user()


app = FastAPI(
    title="SentinelWatch API",
    description="Mini-SOC : détection et réponse aux attaques SSH brute-force",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(websocket.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "project": "SentinelWatch", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    db_type = "sqlite" if settings.database_url.startswith("sqlite") else "postgresql"
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database": db_type,
    }


@app.post("/api/test-attack", tags=["Testing"])
def test_attack(ip: str = "203.45.67.89", attempts: int = 5):
    """
    Endpoint de test : génère des événements d'attaque fictifs
    """
    db = SessionLocal()
    try:
        events_created = []
        for i in range(attempts):
            event = Event(
                timestamp=datetime.utcnow(),
                source_ip=ip,
                username=f"admin_attempt_{i}",
                event_type="FAILED",
                raw_log=f"Test attack attempt {i+1} from {ip}"
            )
            db.add(event)
            events_created.append(event)
        
        db.commit()
        
        return {
            "status": "created",
            "ip": ip,
            "attempts": attempts,
            "events_created": len(events_created)
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


@app.post("/api/seed-demo", tags=["Testing"])
def seed_demo_data():
    """
    Endpoint de démo : génère un jeu de données réaliste pour visualiser le dashboard.
    Idéal pour présenter SentinelWatch à un recruteur sans devoir lancer le worker.
    """
    db = SessionLocal()
    try:
        # Vérifier si des données existent déjà
        existing = db.query(Event).count()
        if existing > 50:
            return {
                "status": "skipped",
                "detail": f"Database already contains {existing} events. Skipping seed.",
            }
        
        # Scénario 1 : Attaque brute-force depuis 203.45.67.89 (déclenche alerte)
        attack_ip = "203.45.67.89"
        base_time = datetime.utcnow() - timedelta(minutes=5)
        for i in range(8):
            event = Event(
                timestamp=base_time + timedelta(seconds=i * 6),
                source_ip=attack_ip,
                username=random.choice(["root", "admin", "ubuntu", "guest"]),
                event_type="FAILED",
                raw_log=f"sshd: Failed password for invalid user from {attack_ip}",
            )
            db.add(event)
        
        # Scénario 2 : Connexions légitimes (mélange réaliste)
        legit_ips = ["10.0.0.15", "10.0.0.22", "192.168.1.45"]
        for i in range(15):
            event = Event(
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(1, 30)),
                source_ip=random.choice(legit_ips),
                username=random.choice(["honore", "analyste", "admin"]),
                event_type=random.choice(["OK", "OK", "OK", "FAILED"]),
                raw_log="sshd: Accepted publickey",
            )
            db.add(event)
        
        # Scénario 3 : Attaque furtive (sous le seuil de détection)
        stealth_ip = "45.67.89.12"
        for i in range(3):
            event = Event(
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(10, 60)),
                source_ip=stealth_ip,
                username="root",
                event_type="FAILED",
                raw_log=f"sshd: Failed password for root from {stealth_ip}",
            )
            db.add(event)
        
        db.commit()
        
        return {
            "status": "seeded",
            "details": {
                "brute_force_attack": "203.45.67.89 (8 events)",
                "legit_connections": "15 events from 3 IPs",
                "stealth_attempts": "45.67.89.12 (3 events under threshold)",
            },
            "tip": "Ouvre le dashboard et observe le flux en temps réel via /ws",
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()
