from __future__ import annotations

from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task, TaskAssignee
from app.modules.tasks.schemas import CalendarDayDto, TaskCreatePayload, TaskDto, TaskUpdatePayload

TERMINAL_STATUSES = {"done", "canceled"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_due_at(due_date: date | None, due_time: time | None) -> datetime | None:
    if due_date is None:
        return None

    effective_time = due_time or time(hour=23, minute=59, second=59)
    return datetime.combine(due_date, effective_time, tzinfo=timezone.utc)


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
    )


def list_calendar_days(db: Session, from_date: date, to_date: date) -> list[CalendarDayDto]:
    rows = db.execute(
        select(Task.due_date, func.count(Task.id))
        .where(Task.due_date.is_not(None), Task.due_date >= from_date, Task.due_date <= to_date)
        .group_by(Task.due_date)
        .order_by(Task.due_date)
    ).all()
    return [CalendarDayDto(date=row[0], count=row[1]) for row in rows]


def list_tasks_for_date(
    db: Session,
    current_user_id: int,
    selected_date: date,
    include_done: bool = False,
) -> list[TaskDto]:
    query = select(Task).where(Task.due_date == selected_date)
    if not include_done:
        query = query.where(Task.status.not_in(["done", "canceled"]))

    tasks = list(db.scalars(query))
    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    now = _now()

    dtos = [_to_dto(task, assignee_map.get(task.id, []), current_user_id, now) for task in tasks]
    return sorted(
        dtos,
        key=lambda item: (
            0 if item.is_overdue else 1,
            item.due_at or datetime.max.replace(tzinfo=timezone.utc),
            item.created_at,
        ),
    )


def create_task(db: Session, current_user_id: int, payload: TaskCreatePayload) -> TaskDto:
    task = Task(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        due_time=payload.due_time,
        due_at=_build_due_at(payload.due_date, payload.due_time),
        status="new",
        urgency=payload.urgency,
        requires_verification=payload.requires_verification,
        verifier_user_id=payload.verifier_user_id,
        created_by_user_id=current_user_id,
        created_at=_now(),
        source_type=payload.source_type,
        source_id=payload.source_id,
    )
    db.add(task)
    for user_id in set(payload.assignee_user_ids):
        db.add(TaskAssignee(task_id=task.id, user_id=user_id))

    db.commit()
    return get_task_dto(db, task.id, current_user_id)


def get_task(db: Session, task_id: str) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id))


def is_user_task_editor(db: Session, task_id: str, user_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    if task.created_by_user_id == user_id:
        return True

    return (
        db.scalar(
            select(TaskAssignee)
            .where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id)
            .limit(1)
        )
        is not None
    )


def get_task_dto(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    assignee_ids = _get_assignee_ids_map(db, [task.id]).get(task.id, [])
    return _to_dto(task, assignee_ids, current_user_id, _now())


def update_task(db: Session, task_id: str, payload: TaskUpdatePayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    updates = payload.model_dump(exclude_unset=True)
    for field in [
        "title",
        "description",
        "urgency",
        "status",
        "requires_verification",
        "verifier_user_id",
        "due_date",
        "due_time",
    ]:
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


def list_attention_tasks(db: Session, current_user_id: int) -> list[TaskDto]:
    now = _now()
    tasks = list(
        db.scalars(
            select(Task).where(
                Task.requires_verification.is_(True),
                Task.verified_at.is_(None),
                Task.due_at.is_not(None),
                Task.due_at < now,
                Task.status.not_in(["done", "canceled"]),
                or_(
                    Task.verifier_user_id == current_user_id,
                    and_(Task.verifier_user_id.is_(None), Task.created_by_user_id == current_user_id),
                ),
            )
        )
    )

    assignee_map = _get_assignee_ids_map(db, [task.id for task in tasks])
    dtos = [_to_dto(task, assignee_map.get(task.id, []), current_user_id, now) for task in tasks]
    return sorted(dtos, key=lambda item: item.due_at or datetime.max.replace(tzinfo=timezone.utc))
