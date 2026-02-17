from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.tasks.schemas import (
    CalendarDayDto,
    FolderCreatePayload,
    FolderDto,
    FolderUpdatePayload,
    RecurrenceActionPayload,
    TaskCreatePayload,
    TaskDto,
    TaskUpdatePayload,
)
from app.modules.tasks.service import (
    complete_task,
    create_folder,
    create_task,
    delete_folder,
    is_user_task_editor,
    list_attention_tasks,
    list_calendar_days,
    list_folders,
    list_tasks_for_date,
    recurrence_action,
    update_folder,
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
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_tasks_for_date(db, current_user.id, date_value, folder_id)


@router.post("", response_model=TaskDto, status_code=status.HTTP_201_CREATED)
def post_task(
    payload: TaskCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskDto:
    try:
        return create_task(db, current_user.id, payload)
    except ValueError as exc:
        if str(exc) == "too_many_recurrence_children":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Слишком длинная серия повторений")
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
        return recurrence_action(db, task_id, payload, current_user.id)
    except ValueError as exc:
        if str(exc) == "task_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        raise


@router.get("/attention", response_model=list[TaskDto])
def get_attention_tasks(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskDto]:
    return list_attention_tasks(db, current_user.id)


@router.get("/folders", response_model=list[FolderDto])
def get_folders(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FolderDto]:
    return list_folders(db, current_user.id)


@router.post("/folders", response_model=FolderDto, status_code=status.HTTP_201_CREATED)
def post_folder(
    payload: FolderCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FolderDto:
    return create_folder(db, current_user.id, payload)


@router.patch("/folders/{folder_id}", response_model=FolderDto)
def patch_folder(
    folder_id: str,
    payload: FolderUpdatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FolderDto:
    try:
        return update_folder(db, folder_id, current_user.id, payload)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Папка не найдена")


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_folder(
    folder_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        delete_folder(db, folder_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Папка не найдена")
