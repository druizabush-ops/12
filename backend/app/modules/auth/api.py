"""HTTP API для аутентификации.
Файл существует для подключения маршрутов регистрации, логина и текущего пользователя.
Минимальность: ровно три endpoint без дополнительных возможностей.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.schemas import Token, UserCreate, UserListItem, UserLogin, UserPublic
from app.modules.auth.security import create_access_token
from app.modules.auth.service import authenticate_user, create_user, get_db, get_user_by_username, list_users_for_picker

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserPublic:
    """Регистрация пользователя.
    Нужна только для создания минимальной учётной записи.
    """

    if get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    user = create_user(db, payload.username, payload.password)
    return UserPublic(id=user.id, username=user.username)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Логин пользователя.
    Возвращает access token для дальнейших запросов.
    """

    # OAuth2PasswordRequestForm не используется, потому что логин оформлен как обычный JSON endpoint.
    # Принимаем Pydantic-схему, чтобы сохранить архитектуру BLOCK 11 без изменений роутера.
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
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
    """Текущий пользователь.
    Минимально читает токен и возвращает технические поля пользователя.
    """

    return UserPublic(id=current_user.id, username=current_user.username)


@router.get("/users", response_model=list[UserListItem])
def users(db: Session = Depends(get_db)) -> list[UserListItem]:
    return list_users_for_picker(db)
