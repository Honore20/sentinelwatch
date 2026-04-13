from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Schéma OAuth2 — indique à FastAPI où trouver le token dans les requêtes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance réutilisable : récupère l'utilisateur connecté depuis son JWT.
    À injecter dans tous les endpoints protégés.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou désactivé"
        )
    return user


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Inscription d'un nouvel analyste SOC."""
    # Vérifie unicité username et email
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Ce username est déjà pris")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Connexion — retourne un JWT si les identifiants sont valides."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return current_user
