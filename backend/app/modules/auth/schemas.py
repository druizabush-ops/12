"""Pydantic-схемы для аутентификации.
Файл нужен для валидации входных данных и ответа без бизнес-деталей.
Минимальность: только логин, пароль и технический ответ токена.
"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Схема регистрации пользователя.
    Описывает минимальные поля для создания учётной записи.
    """

    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    """Схема логина пользователя.
    Используется только для проверки пары логин/пароль.
    """

    username: str
    password: str


class UserPublic(BaseModel):
    """Публичные данные пользователя.
    Минимальны и не содержат никакой чувствительной информации.
    """

    id: int
    username: str


class Token(BaseModel):
    """Ответ с access token.
    Нужен для клиентского хранения и повторного запроса /auth/me.
    """

    access_token: str
    token_type: str = "bearer"
