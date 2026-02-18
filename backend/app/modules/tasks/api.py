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
    TaskBadgeDto,
    TaskCreatePayload,
    TaskDto,
    TaskUpdatePayload,
    TaskUserDto,
)
from app.modules.tasks.service import (
    apply_recurrence_action,
    complete_task,
    create_task,
    delete_recurrence_children,
    delete_task,
    get_task_badges,
    get_task_dto,
    is_user_task_viewer,
    list_calendar_days,
    list_tasks_for_date,
    list_users,
    return_task_to_active,
    update_task,
    verify_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


@router.get("/users", response_model=list[TaskUserDto])
def get_task_users(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskUserDto]:
    _ = current_user
    return list_users(db)


@router.get("/badges", response_model=TaskBadgeDto)
def get_badges(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskBadgeDto:
    return get_task_badges(db, current_user.id)


@router.get("/calendar", response_model=list[CalendarDayDto])
def get_tasks_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    tab: str = Query("assigned"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CalendarDayDto]:
    return list_calendar_days(db, current_user.id, from_date, to_date, tab)


@router.get("", response_model=list[TaskDto])
def get_tasks(
    date_value: date = Query(..., alias="date"),
    tab: str = Query("assigned"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_tasks_for_date(db, current_user.id, date_value, tab)


@router.get("/{task_id}", response_model=TaskDto)
def get_task_by_id(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    if not is_user_task_viewer(db, task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    try:
        return get_task_dto(db, task_id, current_user.id)
    except ValueError:
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
    try:
        return update_task(db, task_id, payload, current_user.id)
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code in {"forbidden", "master_task_edit_forbidden"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        if code == "status_must_be_active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Редактирование доступно только для active")
        raise


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        delete_task(db, task_id, current_user.id)
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code in {"forbidden", "master_has_children"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Удаление недоступно")
        if code == "status_must_be_active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Удаление доступно только для active")
        raise


@router.post("/{task_id}/return-active", response_model=TaskDto)
def post_return_active(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return return_task_to_active(db, task_id, current_user.id)
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Возврат в active невозможен")


@router.post("/{task_id}/complete", response_model=TaskDto)
def post_complete_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return complete_task(db, task_id, current_user.id)
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete доступен только из active")


@router.post("/{task_id}/verify", response_model=TaskDto)
def post_verify_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return verify_task(db, task_id, current_user.id)
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verify доступен только из done_pending_verify")


@router.delete("/{task_id}/recurrence-children", response_model=dict)
def remove_recurrence_children(
    task_id: str,
    mode: str = Query("all"),
    pivot_date: date | None = Query(default=None, alias="date"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        deleted = delete_recurrence_children(db, task_id, current_user.id, mode, pivot_date)
        return {"deleted": deleted}
    except ValueError as exc:
        code = str(exc)
        if code == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if code in {"forbidden", "recurrence_not_supported"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Операция недоступна")
        raise


@router.post("/{task_id}/recurrence-action", response_model=TaskDto)
def post_recurrence_action(
    task_id: str,
    payload: RecurrenceActionPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return apply_recurrence_action(db, task_id, payload, current_user.id)
    except ValueError as exc:
        if str(exc) == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if str(exc) == "recurrence_not_supported":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Задача не является повторяющейся")
        if str(exc) == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise
