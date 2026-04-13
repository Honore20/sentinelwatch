from typing import Optional
from pydantic import BaseModel, field_validator
import re


class UserRegister(BaseModel):
    """Schéma de validation pour l'inscription."""
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Le username doit faire entre 3 et 50 caractères")
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username : lettres, chiffres, - et _ uniquement")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit faire au moins 8 caractères")
        return v


class UserLogin(BaseModel):
    """Schéma de validation pour la connexion."""
    username: str
    password: str


class Token(BaseModel):
    """Réponse renvoyée après une connexion réussie."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Données extraites du JWT décodé."""
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Données utilisateur renvoyées au client (jamais le mot de passe !)."""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True
