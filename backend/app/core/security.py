"""Платформенная зависимость для получения текущего пользователя.
Файл нужен, чтобы централизовать чтение токена и выдачу минимального контекста.
Минимальность: использует auth-модуль без собственной логики JWT и без прав доступа.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.modules.auth.security import decode_access_token
from app.modules.auth.service import get_db, get_user_by_id

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserContext:
    """Возвращает текущего пользователя по access token.
    Реализует только техническую проверку токена и загрузку пользователя.
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
    return UserContext(id=user.id, username=user.username)
