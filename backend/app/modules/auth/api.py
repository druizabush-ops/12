"""HTTP API для аутентификации.
Файл существует для подключения маршрутов регистрации, логина и текущего пользователя.
Минимальность: ровно три endpoint без дополнительных возможностей.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.schemas import Token, UserCreate, UserPublic
from app.modules.auth.security import create_access_token
from app.modules.auth.service import authenticate_user, create_user, get_db, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserPublic:
    if get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    user = create_user(db, payload.username, payload.password)
    return UserPublic(id=user.id, username=user.username, full_name=user.full_name)


@router.post("/login", response_model=Token)
def login(payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, payload.username, payload.password)
    if not user or user.is_archived:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(
    current_user: UserContext = Depends(get_current_user),
) -> UserPublic:
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        is_archived=current_user.is_archived,
        last_organization_id=current_user.last_organization_id,
    )
