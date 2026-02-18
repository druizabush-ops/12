from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.tasks.schemas import (
    CalendarDayDto,
    RecurrenceActionPayload,
    TaskCreatePayload,
    TaskDto,
    TaskUpdatePayload,
)
from app.modules.tasks.service import (
    apply_recurrence_action,
    complete_task,
    create_task,
    get_task_dto,
    is_user_task_editor,
    list_calendar_days,
    list_tasks_for_date,
    update_task,
    verify_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


@router.get("/calendar", response_model=list[CalendarDayDto])
def get_tasks_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CalendarDayDto]:
    return list_calendar_days(db, current_user.id, from_date, to_date)


@router.get("", response_model=list[TaskDto])
def get_tasks(
    date_value: date = Query(..., alias="date"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_tasks_for_date(db, current_user.id, date_value)


@router.get("/{task_id}", response_model=TaskDto)
def get_task_by_id(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    if not is_user_task_editor(db, task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    try:
        return get_task_dto(db, task_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


@router.post("", response_model=TaskDto, status_code=status.HTTP_201_CREATED)
def post_task(
    payload: TaskCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    return create_task(db, current_user.id, payload)


@router.patch("/{task_id}", response_model=TaskDto)
def patch_task(
    task_id: str,
    payload: TaskUpdatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    if not is_user_task_editor(db, task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    try:
        return update_task(db, task_id, payload, current_user.id)
    except ValueError as exc:
        if str(exc) == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        raise


@router.post("/{task_id}/complete", response_model=TaskDto)
def post_complete_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    if not is_user_task_editor(db, task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    try:
        return complete_task(db, task_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


@router.post("/{task_id}/verify", response_model=TaskDto)
def post_verify_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return verify_task(db, task_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if str(exc) == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Подтверждение доступно только создателю или администратору")
        raise


@router.post("/{task_id}/recurrence-action", response_model=TaskDto)
def post_recurrence_action(
    task_id: str,
    payload: RecurrenceActionPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    if not is_user_task_editor(db, task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    try:
        return apply_recurrence_action(db, task_id, payload, current_user.id)
    except ValueError as exc:
        if str(exc) == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if str(exc) == "recurrence_not_supported":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Задача не является повторяющейся")
        raise
