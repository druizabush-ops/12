from __future__ import annotations

from datetime import date, datetime, time, timezone, timedelta
from uuid import uuid4

from sqlalchemy import and_, case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task, TaskAssignee, TaskFolder
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

TERMINAL_STATUSES = {"done", "canceled"}
MAX_RECURRING_GENERATION = 365


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _now().date()


def _build_due_at(due_date: date | None, due_time: time | None) -> datetime | None:
    if due_date is None:
        return None
    effective_time = due_time or time(hour=23, minute=59, second=59)
    return datetime.combine(due_date, effective_time, tzinfo=timezone.utc)


def _weekday_to_int(value: date) -> int:
    return value.weekday()


def _parse_days_of_week(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(v) for v in raw.split(",") if v != ""]


def _serialize_days_of_week(days: list[int]) -> str | None:
    if not days:
        return None
    return ",".join(str(day) for day in sorted(set(days)))


def _get_assignee_ids_map(db: Session, task_ids: list[str]) -> dict[str, list[int]]:
    if not task_ids:
        return {}

    rows = db.execute(
        select(TaskAssignee.task_id, TaskAssignee.user_id).where(TaskAssignee.task_id.in_(task_ids))
    ).all()
    result: dict[str, list[int]] = {task_id: [] for task_id in task_ids}
    for task_id, user_id in rows:
        result.setdefault(task_id, []).append(user_id)
    return result


def _is_overdue(task: Task, today: date) -> bool:
    return bool(task.due_date and task.due_date < today and task.status not in TERMINAL_STATUSES and not task.is_hidden)


def _needs_attention(task: Task, current_user_id: int, is_overdue: bool) -> bool:
    if not is_overdue or not task.requires_verification or task.verified_at is not None:
        return False
    effective_verifier_id = task.verifier_user_id or task.created_by_user_id
    return effective_verifier_id == current_user_id


def _to_dto(task: Task, assignee_ids: list[int], current_user_id: int, today: date) -> TaskDto:
    is_overdue = _is_overdue(task, today)
    return TaskDto(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        due_time=task.due_time,
        due_at=task.due_at,
        status=task.status,
        urgency=task.urgency,
        requires_verification=task.requires_verification,
        verifier_user_id=task.verifier_user_id,
        created_by_user_id=task.created_by_user_id,
        created_at=task.created_at,
        completed_at=task.completed_at,
        verified_at=task.verified_at,
        source_type=task.source_type,
        source_id=task.source_id,
        folder_id=task.folder_id,
        is_recurring=task.is_recurring,
        recurrence_type=task.recurrence_type,
        recurrence_interval=task.recurrence_interval,
        recurrence_days_of_week=_parse_days_of_week(task.recurrence_days_of_week),
        recurrence_end_date=task.recurrence_end_date,
        recurrence_master_task_id=task.recurrence_master_task_id,
        recurrence_state=task.recurrence_state,
        is_hidden=task.is_hidden,
        assignee_user_ids=assignee_ids,
        is_overdue=is_overdue,
        needs_attention_for_verifier=_needs_attention(task, current_user_id, is_overdue),
    )


def _add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    month_lengths = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(value.day, month_lengths[month - 1]))


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)


def _iter_recurrence_dates(start_date: date, payload: TaskCreatePayload) -> list[date]:
    recurrence_type = payload.recurrence_type or "daily"
    interval = payload.recurrence_interval or 1
    end_date = payload.recurrence_end_date or (start_date + timedelta(days=MAX_RECURRING_GENERATION - 1))
    if end_date < start_date:
        return []

    dates: list[date] = []
    current = start_date
    days_of_week = sorted(set(payload.recurrence_days_of_week))

    while current <= end_date:
        if recurrence_type == "daily":
            dates.append(current)
            current = current + timedelta(days=interval)
        elif recurrence_type == "weekly":
            week_start = current - timedelta(days=_weekday_to_int(current))
            week_days = days_of_week or [_weekday_to_int(start_date)]
            for weekday in week_days:
                candidate = week_start + timedelta(days=weekday)
                if candidate < start_date or candidate > end_date:
                    continue
                dates.append(candidate)
            current = current + timedelta(days=7 * interval)
        elif recurrence_type == "monthly":
            dates.append(current)
            current = _add_months(current, interval)
        elif recurrence_type == "yearly":
            dates.append(current)
            current = _add_years(current, interval)
        else:
            break
        if len(set(dates)) > MAX_RECURRING_GENERATION:
            raise ValueError("too_many_recurrence_children")

    unique_dates = sorted(set(dates))
    if len(unique_dates) > MAX_RECURRING_GENERATION:
        raise ValueError("too_many_recurrence_children")
    return unique_dates


def list_calendar_days(db: Session, from_date: date, to_date: date) -> list[CalendarDayDto]:
    completed_day = func.date(Task.completed_at)
    rows = db.execute(
        select(
            Task.due_date.label("day"),
            func.sum(case((and_(Task.status != "done", Task.is_hidden.is_(False)), 1), else_=0)).label("count_active"),
            func.sum(case((and_(Task.status == "done", completed_day == Task.due_date), 1), else_=0)).label("count_done"),
        )
        .where(Task.due_date.is_not(None), Task.due_date >= from_date, Task.due_date <= to_date)
        .group_by(Task.due_date)
        .order_by(Task.due_date)
    ).all()
    return [CalendarDayDto(date=row.day, count_active=int(row.count_active or 0), count_done=int(row.count_done or 0)) for row in rows]


def list_tasks_for_date(db: Session, current_user_id: int, selected_date: date, folder_id: str | None = None) -> list[TaskDto]:
    today = _today()
    folder = None
    if folder_id:
        folder = db.scalar(
            select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id)
        )

    show_active = True if folder is None else folder.show_active
    show_overdue = True if folder is None else folder.show_overdue
    show_done = True if folder is None else folder.show_done

    conditions = []
    if show_active:
        conditions.append(and_(Task.due_date == selected_date, Task.status != "done", Task.is_hidden.is_(False)))
    if show_overdue:
        conditions.append(and_(Task.due_date < today, Task.status != "done", Task.is_hidden.is_(False)))
    if show_done:
        conditions.append(Task.status == "done")

    if not conditions:
        return []

    query = select(Task).where(or_(*conditions))
    if folder_id:
        query = query.where(Task.folder_id == folder_id)

    tasks = list(db.scalars(query.order_by(Task.status, Task.due_date, Task.created_at)))
    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    return [_to_dto(task, assignee_map.get(task.id, []), current_user_id, today) for task in tasks]


def _build_task_entity(task_id: str, payload: TaskCreatePayload, current_user_id: int, due_date: date | None, master_id: str | None) -> Task:
    recurrence_interval = payload.recurrence_interval or 1
    recurrence_type = payload.recurrence_type or "daily"
    is_recurring = payload.is_recurring or payload.due_date is None
    recurrence_master_task_id = master_id
    return Task(
        id=task_id,
        title=payload.title,
        description=payload.description,
        due_date=due_date,
        due_time=payload.due_time,
        due_at=_build_due_at(due_date, payload.due_time),
        status="new",
        urgency=payload.urgency,
        requires_verification=payload.requires_verification,
        verifier_user_id=payload.verifier_user_id,
        created_by_user_id=current_user_id,
        created_at=_now(),
        source_type=payload.source_type,
        source_id=payload.source_id,
        folder_id=payload.folder_id,
        is_recurring=is_recurring,
        recurrence_type=recurrence_type if is_recurring else None,
        recurrence_interval=recurrence_interval if is_recurring else None,
        recurrence_days_of_week=_serialize_days_of_week(payload.recurrence_days_of_week),
        recurrence_end_date=payload.recurrence_end_date,
        recurrence_master_task_id=recurrence_master_task_id,
        recurrence_state="active" if is_recurring else "stopped",
        is_hidden=False,
    )


def create_task(db: Session, current_user_id: int, payload: TaskCreatePayload) -> TaskDto:
    effective_payload = payload.model_copy(deep=True)
    if effective_payload.due_date is None:
        effective_payload.due_date = _today()
        effective_payload.is_recurring = True
        effective_payload.recurrence_type = "daily"
        effective_payload.recurrence_interval = 1
        effective_payload.recurrence_end_date = effective_payload.due_date + timedelta(days=MAX_RECURRING_GENERATION - 1)

    task_id = str(uuid4())
    master_task = _build_task_entity(task_id, effective_payload, current_user_id, effective_payload.due_date, None)
    db.add(master_task)

    recurrence_dates: list[date] = []
    if master_task.is_recurring:
        recurrence_dates = _iter_recurrence_dates(effective_payload.due_date, effective_payload)
        for recurrence_date in recurrence_dates:
            if recurrence_date == effective_payload.due_date:
                continue
            child_task = _build_task_entity(str(uuid4()), effective_payload, current_user_id, recurrence_date, task_id)
            db.add(child_task)

    for user_id in set(effective_payload.assignee_user_ids):
        db.add(TaskAssignee(task_id=task_id, user_id=user_id))

    if len(recurrence_dates) > MAX_RECURRING_GENERATION:
        raise ValueError("too_many_recurrence_children")

    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def get_task(db: Session, task_id: str) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id))


def is_user_task_editor(db: Session, task_id: str, user_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    if task.created_by_user_id == user_id:
        return True
    return db.scalar(select(TaskAssignee).where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id).limit(1)) is not None


def get_task_dto(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    assignee_ids = _get_assignee_ids_map(db, [task.id]).get(task.id, [])
    return _to_dto(task, assignee_ids, current_user_id, _today())


def update_task(db: Session, task_id: str, payload: TaskUpdatePayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    updates = payload.model_dump(exclude_unset=True)
    for field in ["title", "description", "urgency", "status", "requires_verification", "verifier_user_id", "due_date", "due_time", "folder_id", "is_hidden"]:
        if field in updates:
            setattr(task, field, updates[field])

    if "due_date" in updates or "due_time" in updates:
        task.due_at = _build_due_at(task.due_date, task.due_time)

    if "status" in updates and updates["status"] == "done":
        task.completed_at = _now()

    if payload.assignee_user_ids is not None:
        db.query(TaskAssignee).filter(TaskAssignee.task_id == task_id).delete()
        for user_id in set(payload.assignee_user_ids):
            db.add(TaskAssignee(task_id=task_id, user_id=user_id))

    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def complete_task(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    task.status = "done"
    task.completed_at = _now()
    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def verify_task(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if not task.requires_verification:
        raise ValueError("verification_not_required")
    verifier_id = task.verifier_user_id or task.created_by_user_id
    if verifier_id != current_user_id:
        raise ValueError("forbidden")
    task.verified_at = _now()
    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def recurrence_action(db: Session, task_id: str, payload: RecurrenceActionPayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    master_task = task
    if task.recurrence_master_task_id:
        master_task = get_task(db, task.recurrence_master_task_id)
        if not master_task:
            raise ValueError("task_not_found")

    today = _today()
    future_children_query = select(Task).where(Task.recurrence_master_task_id == master_task.id, Task.due_date > today)
    future_children = list(db.scalars(future_children_query))

    if payload.action == "pause":
        master_task.recurrence_state = "paused"
        for child in future_children:
            child.is_hidden = True
    elif payload.action == "resume":
        master_task.recurrence_state = "active"
        for child in future_children:
            child.is_hidden = False
    elif payload.action == "stop":
        master_task.recurrence_state = "stopped"
        db.execute(delete(Task).where(Task.recurrence_master_task_id == master_task.id, Task.due_date > today))
    db.commit()
    return get_task_dto(db, master_task.id, current_user_id)


def list_attention_tasks(db: Session, current_user_id: int) -> list[TaskDto]:
    today = _today()
    tasks = list(
        db.scalars(
            select(Task).where(
                Task.requires_verification.is_(True),
                Task.verified_at.is_(None),
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status.not_in(["done", "canceled"]),
                Task.is_hidden.is_(False),
                or_(
                    Task.verifier_user_id == current_user_id,
                    and_(Task.verifier_user_id.is_(None), Task.created_by_user_id == current_user_id),
                ),
            )
        )
    )

    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    return sorted([_to_dto(task, assignee_map.get(task.id, []), current_user_id, today) for task in tasks], key=lambda item: item.due_date or date.max)


def list_folders(db: Session, current_user_id: int) -> list[FolderDto]:
    folders = list(db.scalars(select(TaskFolder).where(TaskFolder.created_by_user_id == current_user_id).order_by(TaskFolder.created_at)))
    return [FolderDto.model_validate(folder, from_attributes=True) for folder in folders]


def create_folder(db: Session, current_user_id: int, payload: FolderCreatePayload) -> FolderDto:
    folder = TaskFolder(id=str(uuid4()), title=payload.title, created_by_user_id=current_user_id, created_at=_now(), show_active=True, show_overdue=True, show_done=True)
    db.add(folder)
    db.commit()
    return FolderDto.model_validate(folder, from_attributes=True)


def update_folder(db: Session, folder_id: str, current_user_id: int, payload: FolderUpdatePayload) -> FolderDto:
    folder = db.scalar(select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id))
    if not folder:
        raise ValueError("folder_not_found")
    updates = payload.model_dump(exclude_unset=True)
    for field in ["title", "show_active", "show_overdue", "show_done"]:
        if field in updates:
            setattr(folder, field, updates[field])
    db.commit()
    return FolderDto.model_validate(folder, from_attributes=True)


def delete_folder(db: Session, folder_id: str, current_user_id: int) -> None:
    folder = db.scalar(select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id))
    if not folder:
        raise ValueError("folder_not_found")
    db.execute(delete(Task).where(Task.folder_id == folder_id))
    db.delete(folder)
    db.commit()
