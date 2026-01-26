"""HTTP API для аутентификации.
Файл существует для подключения маршрутов регистрации, логина и текущего пользователя.
Минимальность: ровно три endpoint без дополнительных возможностей.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.schemas import Token, UserCreate, UserLogin, UserPublic
from app.modules.auth.security import create_access_token, decode_access_token
from app.modules.auth.service import (
    authenticate_user,
    create_user,
    get_db,
    get_user_by_id,
    get_user_by_username,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Текущий пользователь.
    Минимально читает токен и возвращает технические поля пользователя.
    """

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return UserPublic(id=user.id, username=user.username)
