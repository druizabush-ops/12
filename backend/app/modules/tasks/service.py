from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task, TaskAssignee, TaskFolder
from app.modules.tasks.schemas import (
    CalendarDayDto,
    RecurrenceActionPayload,
    TaskCreatePayload,
    TaskDto,
    TaskFolderCreatePayload,
    TaskFolderDto,
    TaskFolderUpdatePayload,
    TaskUpdatePayload,
)

TERMINAL_STATUSES = {"done", "canceled"}
FOLDER_FILTER_KEYS = {
    "assignee_user_id",
    "verifier_user_id",
    "urgency",
    "requires_verification",
    "status",
    "source_type",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _now().date()


def _build_due_at(due_date: date | None, due_time: time | None) -> datetime | None:
    if due_date is None:
        return None
    effective_time = due_time or time(hour=23, minute=59, second=59)
    return datetime.combine(due_date, effective_time, tzinfo=timezone.utc)


def _task_visibility_filter(current_user_id: int):
    return or_(
        Task.created_by_user_id == current_user_id,
        exists(select(TaskAssignee.task_id).where(TaskAssignee.task_id == Task.id, TaskAssignee.user_id == current_user_id)),
    )


def _add_interval(source: date, recurrence_type: str, recurrence_interval: int) -> date:
    if recurrence_type == "daily":
        return source + timedelta(days=recurrence_interval)
    if recurrence_type == "weekly":
        return source + timedelta(weeks=recurrence_interval)
    if recurrence_type == "monthly":
        month_index = (source.month - 1) + recurrence_interval
        year = source.year + month_index // 12
        month = month_index % 12 + 1
        day = min(source.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    year = source.year + recurrence_interval
    day = min(source.day, calendar.monthrange(year, source.month)[1])
    return date(year, source.month, day)


def _build_occurrences(master: Task, from_date: date, horizon_date: date) -> list[date]:
    recurrence_type = master.recurrence_type or "daily"
    recurrence_interval = master.recurrence_interval or 1
    current = master.due_date or from_date
    end_limit = horizon_date
    if master.recurrence_end_date and master.recurrence_end_date < end_limit:
        end_limit = master.recurrence_end_date

    dates: list[date] = []
    while current <= end_limit:
        if current >= from_date:
            if recurrence_type == "weekly" and master.recurrence_days_of_week:
                if current.isoweekday() in master.recurrence_days_of_week:
                    dates.append(current)
            else:
                dates.append(current)
        current = _add_interval(current, recurrence_type, recurrence_interval)
    return dates


def _get_assignee_ids_map(db: Session, task_ids: list[str]) -> dict[str, list[int]]:
    if not task_ids:
        return {}
    rows = db.execute(select(TaskAssignee.task_id, TaskAssignee.user_id).where(TaskAssignee.task_id.in_(task_ids))).all()
    result: dict[str, list[int]] = {task_id: [] for task_id in task_ids}
    for task_id, user_id in rows:
        result.setdefault(task_id, []).append(user_id)
    return result


def _is_overdue(task: Task, now: datetime) -> bool:
    return bool(task.due_at and now > task.due_at and task.status not in TERMINAL_STATUSES)


def _needs_attention(task: Task, current_user_id: int, is_overdue: bool) -> bool:
    if not is_overdue or not task.requires_verification or task.verified_at is not None:
        return False
    effective_verifier_id = task.verifier_user_id or task.created_by_user_id
    return effective_verifier_id == current_user_id


def _to_dto(task: Task, assignee_ids: list[int], current_user_id: int, now: datetime) -> TaskDto:
    is_overdue = _is_overdue(task, now)
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
        assignee_user_ids=assignee_ids,
        is_overdue=is_overdue,
        needs_attention_for_verifier=_needs_attention(task, current_user_id, is_overdue),
        is_recurring=task.is_recurring,
        recurrence_type=task.recurrence_type,
        recurrence_interval=task.recurrence_interval,
        recurrence_days_of_week=task.recurrence_days_of_week,
        recurrence_end_date=task.recurrence_end_date,
        recurrence_master_task_id=task.recurrence_master_task_id,
        recurrence_state=task.recurrence_state,
        is_hidden=task.is_hidden,
    )


def _apply_allowed_folder_filter(query, filter_json: dict):
    for key, value in filter_json.items():
        if key not in FOLDER_FILTER_KEYS or value is None:
            continue
        if key == "assignee_user_id":
            query = query.where(
                exists(select(TaskAssignee.task_id).where(TaskAssignee.task_id == Task.id, TaskAssignee.user_id == int(value)))
            )
        elif key == "verifier_user_id":
            query = query.where(Task.verifier_user_id == int(value))
        elif key == "urgency":
            query = query.where(Task.urgency == str(value))
        elif key == "requires_verification":
            query = query.where(Task.requires_verification.is_(bool(value)))
        elif key == "status":
            query = query.where(Task.status == str(value))
        elif key == "source_type":
            query = query.where(Task.source_type == str(value))
    return query


def _copy_assignees(db: Session, source_task_id: str, target_task_id: str) -> None:
    ids = db.scalars(select(TaskAssignee.user_id).where(TaskAssignee.task_id == source_task_id)).all()
    for user_id in set(ids):
        db.add(TaskAssignee(task_id=target_task_id, user_id=user_id))


def _generate_children(db: Session, master: Task, from_date: date, horizon_days: int = 365) -> None:
    horizon = from_date + timedelta(days=horizon_days)
    dates = _build_occurrences(master, from_date, horizon)
    if len(dates) > 365:
        raise ValueError("recurrence_limit_exceeded")

    existing_dates = set(
        db.scalars(
            select(Task.due_date).where(
                Task.recurrence_master_task_id == master.id,
                Task.due_date.is_not(None),
            )
        ).all()
    )

    for due_date in dates:
        if due_date in existing_dates or due_date == master.due_date:
            continue
        child_id = str(uuid4())
        db.add(
            Task(
                id=child_id,
                title=master.title,
                description=master.description,
                due_date=due_date,
                due_time=master.due_time,
                due_at=_build_due_at(due_date, master.due_time),
                status="new",
                urgency=master.urgency,
                requires_verification=master.requires_verification,
                verifier_user_id=master.verifier_user_id,
                created_by_user_id=master.created_by_user_id,
                created_at=_now(),
                source_type=master.source_type,
                source_id=master.source_id,
                is_recurring=False,
                recurrence_master_task_id=master.id,
                is_hidden=master.recurrence_state == "paused",
            )
        )
        _copy_assignees(db, master.id, child_id)


def _ensure_recurrence_horizon(db: Session, current_user_id: int) -> None:
    masters = list(
        db.scalars(
            select(Task).where(
                Task.is_recurring.is_(True),
                Task.recurrence_state == "active",
                _task_visibility_filter(current_user_id),
            )
        )
    )
    today = _today()
    for master in masters:
        max_child_due = db.scalar(
            select(func.max(Task.due_date)).where(
                Task.recurrence_master_task_id == master.id,
                Task.is_hidden.is_(False),
            )
        )
        if max_child_due is None or max_child_due < today + timedelta(days=30):
            _generate_children(db, master, today)
    db.commit()


def list_calendar_days(db: Session, current_user_id: int, from_date: date, to_date: date) -> list[CalendarDayDto]:
    rows = db.execute(
        select(Task.due_date, func.count(Task.id))
        .where(
            Task.due_date.is_not(None),
            Task.due_date >= from_date,
            Task.due_date <= to_date,
            Task.status != "done",
            Task.is_hidden.is_(False),
            _task_visibility_filter(current_user_id),
        )
        .group_by(Task.due_date)
        .order_by(Task.due_date)
    ).all()
    return [CalendarDayDto(date=row[0], count=row[1]) for row in rows]


def list_tasks_for_date(db: Session, current_user_id: int, selected_date: date, folder_id: str | None = None) -> list[TaskDto]:
    _ensure_recurrence_horizon(db, current_user_id)
    today = _today()

    query = select(Task).where(
        _task_visibility_filter(current_user_id),
        Task.is_hidden.is_(False),
        or_(
            Task.due_date == selected_date,
            and_(Task.due_date < today, Task.status != "done"),
        ),
    )

    if folder_id:
        folder = db.scalar(
            select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id)
        )
        if not folder:
            raise ValueError("folder_not_found")
        query = _apply_allowed_folder_filter(query, folder.filter_json or {})

    tasks = list(db.scalars(query))
    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    now = _now()
    dtos = [_to_dto(task, assignee_map.get(task.id, []), current_user_id, now) for task in tasks]
    return sorted(dtos, key=lambda item: (item.status == "done", item.due_at or datetime.max.replace(tzinfo=timezone.utc), item.created_at))


def _build_master_from_payload(current_user_id: int, payload: TaskCreatePayload) -> Task:
    start_due_date = payload.due_date or _today()
    recurrence_enabled = payload.is_recurring or payload.due_date is None
    recurrence_type = payload.recurrence_type or "daily"
    recurrence_interval = payload.recurrence_interval or 1
    recurrence_state = "active" if recurrence_enabled else None

    return Task(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        due_date=start_due_date,
        due_time=payload.due_time,
        due_at=_build_due_at(start_due_date, payload.due_time),
        status="new",
        urgency=payload.urgency,
        requires_verification=payload.requires_verification,
        verifier_user_id=payload.verifier_user_id,
        created_by_user_id=current_user_id,
        created_at=_now(),
        source_type=payload.source_type,
        source_id=payload.source_id,
        is_recurring=recurrence_enabled,
        recurrence_type=recurrence_type if recurrence_enabled else None,
        recurrence_interval=recurrence_interval if recurrence_enabled else None,
        recurrence_days_of_week=payload.recurrence_days_of_week if recurrence_enabled else None,
        recurrence_end_date=payload.recurrence_end_date if recurrence_enabled else None,
        recurrence_state=recurrence_state,
        is_hidden=False,
    )


def create_task(db: Session, current_user_id: int, payload: TaskCreatePayload) -> TaskDto:
    task = _build_master_from_payload(current_user_id, payload)
    db.add(task)

    assignees = set(payload.assignee_user_ids)
    if not assignees:
        assignees = {current_user_id}
    for user_id in assignees:
        db.add(TaskAssignee(task_id=task.id, user_id=user_id))

    db.flush()
    if task.is_recurring:
        _generate_children(db, task, _today())

    db.commit()
    return get_task_dto(db, task.id, current_user_id)


def get_task(db: Session, task_id: str) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id))


def _get_master(task: Task, db: Session) -> Task:
    if task.recurrence_master_task_id:
        master = get_task(db, task.recurrence_master_task_id)
        return master or task
    return task


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
    return _to_dto(task, assignee_ids, current_user_id, _now())


def _apply_updates(task: Task, payload: TaskUpdatePayload) -> None:
    updates = payload.model_dump(exclude_unset=True)
    for field in ["title", "description", "urgency", "status", "requires_verification", "verifier_user_id", "due_date", "due_time"]:
        if field in updates:
            setattr(task, field, updates[field])
    if "due_date" in updates or "due_time" in updates:
        task.due_at = _build_due_at(task.due_date, task.due_time)
    if "status" in updates and updates["status"] == "done":
        task.completed_at = _now()


def update_task(db: Session, task_id: str, payload: TaskUpdatePayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    scope = payload.apply_scope
    if scope == "single" or not (task.is_recurring or task.recurrence_master_task_id):
        targets = [task]
    else:
        master = _get_master(task, db)
        if scope == "future":
            anchor_date = task.due_date or _today()
            targets = list(
                db.scalars(
                    select(Task).where(
                        or_(Task.id == master.id, Task.recurrence_master_task_id == master.id),
                        Task.due_date >= anchor_date,
                    )
                )
            )
        else:
            _apply_updates(master, payload)
            db.query(Task).filter(
                Task.recurrence_master_task_id == master.id,
                Task.due_date > _today(),
            ).delete()
            _generate_children(db, master, _today())
            targets = [master]

    for target in targets:
        _apply_updates(target, payload)

    if payload.assignee_user_ids is not None:
        assignee_set = set(payload.assignee_user_ids)
        if not assignee_set:
            assignee_set = {current_user_id}
        for target in targets:
            db.query(TaskAssignee).filter(TaskAssignee.task_id == target.id).delete()
            for user_id in assignee_set:
                db.add(TaskAssignee(task_id=target.id, user_id=user_id))

    db.commit()
    return get_task_dto(db, task.id, current_user_id)


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


def list_attention_tasks(db: Session, current_user_id: int) -> list[TaskDto]:
    now = _now()
    tasks = list(
        db.scalars(
            select(Task).where(
                Task.is_hidden.is_(False),
                Task.requires_verification.is_(True),
                Task.verified_at.is_(None),
                Task.due_at.is_not(None),
                Task.due_at < now,
                Task.status.not_in(["done", "canceled"]),
                or_(Task.verifier_user_id == current_user_id, and_(Task.verifier_user_id.is_(None), Task.created_by_user_id == current_user_id)),
            )
        )
    )
    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    dtos = [_to_dto(task, assignee_map.get(task.id, []), current_user_id, now) for task in tasks]
    return sorted(dtos, key=lambda item: item.due_at or datetime.max.replace(tzinfo=timezone.utc))


def recurrence_action(db: Session, task_id: str, payload: RecurrenceActionPayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    master = _get_master(task, db)
    if not master.is_recurring:
        raise ValueError("not_recurring")

    today = _today()
    if payload.action == "pause":
        master.recurrence_state = "paused"
        db.query(Task).filter(Task.recurrence_master_task_id == master.id, Task.due_date > today).update({Task.is_hidden: True})
    elif payload.action == "resume":
        master.recurrence_state = "active"
        db.query(Task).filter(Task.recurrence_master_task_id == master.id, Task.due_date > today).update({Task.is_hidden: False})
        _generate_children(db, master, today)
    else:
        master.recurrence_state = "stopped"
        db.query(Task).filter(Task.recurrence_master_task_id == master.id, Task.due_date > today).delete()

    db.commit()
    return get_task_dto(db, master.id, current_user_id)


def list_folders(db: Session, current_user_id: int) -> list[TaskFolderDto]:
    folders = list(
        db.scalars(
            select(TaskFolder).where(TaskFolder.created_by_user_id == current_user_id).order_by(TaskFolder.created_at.desc())
        )
    )
    return [TaskFolderDto(id=folder.id, name=folder.name, created_by_user_id=folder.created_by_user_id, filter_json=folder.filter_json or {}, created_at=folder.created_at) for folder in folders]


def create_folder(db: Session, current_user_id: int, payload: TaskFolderCreatePayload) -> TaskFolderDto:
    folder = TaskFolder(
        id=str(uuid4()),
        name=payload.name,
        created_by_user_id=current_user_id,
        filter_json={k: v for k, v in payload.filter_json.items() if k in FOLDER_FILTER_KEYS},
        created_at=_now(),
    )
    db.add(folder)
    db.commit()
    return TaskFolderDto(id=folder.id, name=folder.name, created_by_user_id=folder.created_by_user_id, filter_json=folder.filter_json or {}, created_at=folder.created_at)


def update_folder(db: Session, folder_id: str, current_user_id: int, payload: TaskFolderUpdatePayload) -> TaskFolderDto:
    folder = db.scalar(select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id))
    if not folder:
        raise ValueError("folder_not_found")
    if payload.name is not None:
        folder.name = payload.name
    if payload.filter_json is not None:
        folder.filter_json = {k: v for k, v in payload.filter_json.items() if k in FOLDER_FILTER_KEYS}
    db.commit()
    return TaskFolderDto(id=folder.id, name=folder.name, created_by_user_id=folder.created_by_user_id, filter_json=folder.filter_json or {}, created_at=folder.created_at)


def delete_folder(db: Session, folder_id: str, current_user_id: int) -> None:
    folder = db.scalar(select(TaskFolder).where(TaskFolder.id == folder_id, TaskFolder.created_by_user_id == current_user_id))
    if not folder:
        raise ValueError("folder_not_found")
    db.delete(folder)
    db.commit()
