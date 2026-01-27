"""API тестового модуля.
Файл нужен для демонстрации собственного router'а модуля.
Минимальность: только один технический endpoint без бизнес-логики.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/dummy", tags=["dummy"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Техническая проверка доступности.
    Нужна для демонстрации подключения модуля.
    Минимальность: возвращает фиксированный ответ.
    """

    return {"status": "ok"}
