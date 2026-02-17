from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.tasks.schemas import (
    CalendarDayDto,
    TaskCreatePayload,
    TaskDto,
    TaskFolderCreatePayload,
    TaskFolderDto,
    TaskUpdatePayload,
)
from app.modules.tasks.service import (
    complete_task,
    create_task,
    create_task_folder,
    is_user_task_editor,
    list_attention_tasks,
    list_calendar_days,
    list_task_folders,
    list_tasks_for_date,
    update_task,
    verify_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


@router.get("/calendar", response_model=list[CalendarDayDto])
def get_tasks_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
) -> list[CalendarDayDto]:
    return list_calendar_days(db, from_date, to_date)


@router.get("", response_model=list[TaskDto])
def get_tasks(
    date_value: date = Query(..., alias="date"),
    folder_id: str | None = Query(default=None),
    include_done: bool = Query(True),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_tasks_for_date(db, current_user.id, date_value, folder_id, include_done)


@router.get("/folders", response_model=list[TaskFolderDto])
def get_task_folders(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskFolderDto]:
    return list_task_folders(db, current_user.id)


@router.post("/folders", response_model=TaskFolderDto, status_code=status.HTTP_201_CREATED)
def post_task_folder(
    payload: TaskFolderCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskFolderDto:
    return create_task_folder(db, current_user.id, payload)


@router.post("", response_model=TaskDto, status_code=status.HTTP_201_CREATED)
def post_task(
    payload: TaskCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return create_task(db, current_user.id, payload)
    except ValueError as exc:
        if str(exc) == "recurrence_limit_exceeded":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recurrence_limit_exceeded")
        raise


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
    except ValueError:
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
        if str(exc) == "verification_not_required":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Проверка не требуется")
        if str(exc) == "forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        raise


@router.get("/attention", response_model=list[TaskDto])
def get_attention_tasks(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_attention_tasks(db, current_user.id)
