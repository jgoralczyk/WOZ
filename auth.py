"""
System autentykacji JWT dla aplikacji WOZ.
Obsługuje rejestrację, logowanie i zarządzanie użytkownikami.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from database import get_session
from models import User

# Konfiguracja JWT
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security
security = HTTPBearer()


class UserRegister(BaseModel):
    """Schema do rejestracji użytkownika."""
    email: EmailStr
    password: str
    full_name: str
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Hasło musi mieć minimum 8 znaków')
        return v


class UserLogin(BaseModel):
    """Schema do logowania."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema odpowiedzi z danymi użytkownika (bez hasła)."""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    """Schema odpowiedzi z tokenami."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema do odświeżania tokena."""
    refresh_token: str


# ============== FUNKCJE POMOCNICZE ==============

def hash_password(password: str) -> str:
    """Hashuje hasło używając bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikuje hasło."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tworzy access token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Tworzy refresh token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Dekoduje token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token nieprawidłowy lub wygasł",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Pobiera użytkownika po email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Pobiera użytkownika po ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


# ============== DEPENDENCY: CURRENT USER ==============

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Dependency do pobierania aktualnie zalogowanego użytkownika."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy typ tokena"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token nie zawiera ID użytkownika"
        )
    
    user = await get_user_by_id(session, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie istnieje"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto użytkownika jest nieaktywne"
        )
    
    return user


def require_role(allowed_roles: list[str]):
    """Dependency factory do sprawdzania roli użytkownika."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Wymagana rola: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# ============== ROUTER ==============

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """Rejestracja nowego użytkownika."""
    # Sprawdź czy email już istnieje
    existing_user = await get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik z tym adresem email już istnieje"
        )
    
    # Utwórz użytkownika
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="user"
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    # Generuj tokeny
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """Logowanie użytkownika."""
    user = await get_user_by_email(session, credentials.email)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto użytkownika jest nieaktywne"
        )
    
    # Generuj tokeny
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Odświeżenie access tokena."""
    payload = decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy typ tokena"
        )
    
    user_id = payload.get("sub")
    user = await get_user_by_id(session, int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie istnieje lub jest nieaktywny"
        )
    
    # Generuj nowe tokeny
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Pobierz dane aktualnie zalogowanego użytkownika."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active
    )
