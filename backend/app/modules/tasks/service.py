from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.admin_access.service import user_can_manage_access
from app.modules.auth.models import User
from app.modules.tasks.models import Task, TaskAssignee
from app.modules.tasks.schemas import (
    CalendarDayDto,
    RecurrenceActionPayload,
    TaskBadgesDto,
    TaskCreatePayload,
    TaskDto,
    TaskUpdatePayload,
)

DONE_STATUS = "done"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _priority_weight(priority: str | None) -> int:
    return {"very_urgent": 3, "urgent": 2, "normal": 1}.get(priority or "", 0)


def _advance_date(current: date, recurrence_type: str, recurrence_interval: int) -> date:
    if recurrence_type == "daily":
        return current.fromordinal(current.toordinal() + recurrence_interval)
    if recurrence_type == "weekly":
        return current.fromordinal(current.toordinal() + 7 * recurrence_interval)

    if recurrence_type == "yearly":
        year = current.year + recurrence_interval
        day = min(current.day, monthrange(year, current.month)[1])
        return date(year, current.month, day)

    # monthly
    month_index = current.month - 1 + recurrence_interval
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, monthrange(year, month)[1])
    return date(year, month, day)


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


def _get_usernames_map(db: Session, user_ids: list[int]) -> dict[int, str]:
    unique_ids = sorted(set(user_ids))
    if not unique_ids:
        return {}

    rows = db.execute(select(User.id, User.username).where(User.id.in_(unique_ids))).all()
    return {user_id: username for user_id, username in rows}


def _is_overdue(task: Task, now_local: datetime) -> bool:
    if task.status == DONE_STATUS or task.is_hidden or not task.due_date:
        return False

    today = now_local.date()
    if task.due_date < today:
        return True
    if task.due_date > today:
        return False
    if task.due_time is None:
        return False
    return task.due_time < now_local.time().replace(tzinfo=None)


def _to_dto(task: Task, assignee_ids: list[int], usernames_map: dict[int, str], now_local: datetime) -> TaskDto:
    return TaskDto(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        due_time=task.due_time,
        status=task.status,
        priority=task.priority,
        verifier_user_id=task.verifier_user_id,
        verifier_name=usernames_map.get(task.verifier_user_id) if task.verifier_user_id else None,
        created_by_user_id=task.created_by_user_id,
        created_by_name=usernames_map.get(task.created_by_user_id, f"ID {task.created_by_user_id}"),
        created_at=task.created_at,
        completed_at=task.completed_at,
        verified_at=task.verified_at,
        source_type=task.source_type,
        source_id=task.source_id,
        assignee_user_ids=assignee_ids,
        assignee_names=[usernames_map.get(user_id, f"ID {user_id}") for user_id in assignee_ids],
        is_overdue=_is_overdue(task, now_local),
        is_recurring=task.is_recurring,
        recurrence_type=task.recurrence_type,
        recurrence_interval=task.recurrence_interval,
        recurrence_days_of_week=task.recurrence_days_of_week,
        recurrence_end_date=task.recurrence_end_date,
        recurrence_master_task_id=task.recurrence_master_task_id,
        recurrence_state=task.recurrence_state,
        is_hidden=task.is_hidden,
    )


def _generate_recurrence_children(db: Session, master_task: Task, assignee_ids: list[int]) -> None:
    if not master_task.is_recurring or not master_task.due_date or not master_task.recurrence_type:
        return

    interval = master_task.recurrence_interval or 1
    current_date = master_task.due_date
    limit = 365

    for _ in range(limit):
        current_date = _advance_date(current_date, master_task.recurrence_type, interval)
        if master_task.recurrence_end_date and current_date > master_task.recurrence_end_date:
            break

        child = Task(
            id=str(uuid4()),
            title=master_task.title,
            description=master_task.description,
            due_date=current_date,
            due_time=master_task.due_time,
            status="active",
            priority=master_task.priority,
            verifier_user_id=master_task.verifier_user_id,
            created_by_user_id=master_task.created_by_user_id,
            created_at=_now(),
            source_type=master_task.source_type,
            source_id=master_task.source_id,
            is_recurring=False,
            recurrence_master_task_id=master_task.id,
            recurrence_state=master_task.recurrence_state,
            is_hidden=master_task.recurrence_state == "paused",
        )
        db.add(child)
        db.flush()

        for assignee_id in assignee_ids:
            db.add(TaskAssignee(task_id=child.id, user_id=assignee_id))


def _visible_task_filter(current_user_id: int):
    return or_(
        Task.created_by_user_id == current_user_id,
        exists(select(TaskAssignee.task_id).where(TaskAssignee.task_id == Task.id, TaskAssignee.user_id == current_user_id)),
    )


def list_calendar_days(db: Session, current_user_id: int, from_date: date, to_date: date) -> list[CalendarDayDto]:
    is_admin = user_can_manage_access(db, current_user_id)

    query = (
        select(Task.due_date, func.count(Task.id))
        .where(
            Task.due_date.is_not(None),
            Task.due_date >= from_date,
            Task.due_date <= to_date,
            Task.status != DONE_STATUS,
            Task.is_hidden.is_(False),
        )
        .group_by(Task.due_date)
        .order_by(Task.due_date)
    )

    if not is_admin:
        query = query.where(_visible_task_filter(current_user_id))

    rows = db.execute(query).all()
    return [CalendarDayDto(date=row[0], count=row[1]) for row in rows]


def list_tasks_for_date(db: Session, current_user_id: int, selected_date: date) -> list[TaskDto]:
    is_admin = user_can_manage_access(db, current_user_id)
    visibility_filter = _visible_task_filter(current_user_id)

    active_query = select(Task).where(
        Task.due_date == selected_date,
        Task.status == "active",
        Task.is_hidden.is_(False),
    )
    done_query = select(Task).where(
        Task.due_date == selected_date,
        Task.status == DONE_STATUS,
        Task.is_hidden.is_(False),
    )

    now_local = _now_local()
    today = now_local.date()
    now_time = now_local.time().replace(tzinfo=None)

    overdue_query = select(Task).where(
        Task.status == "active",
        Task.is_hidden.is_(False),
        or_(
            Task.due_date < today,
            Task.due_date == today,
        ),
        or_(
            Task.due_date < today,
            and_(Task.due_date == today, Task.due_time.is_not(None), Task.due_time < now_time),
        ),
    )

    if not is_admin:
        active_query = active_query.where(visibility_filter)
        overdue_query = overdue_query.where(visibility_filter)
        done_query = done_query.where(visibility_filter)

    active_tasks = list(db.scalars(active_query))
    overdue_tasks = list(db.scalars(overdue_query))
    done_tasks = list(db.scalars(done_query))

    all_tasks = active_tasks + overdue_tasks + done_tasks
    assignee_map = _get_assignee_ids_map(db, [task.id for task in all_tasks])
    user_ids: list[int] = []
    for task in all_tasks:
        user_ids.append(task.created_by_user_id)
        if task.verifier_user_id:
            user_ids.append(task.verifier_user_id)
        user_ids.extend(assignee_map.get(task.id, []))
    usernames_map = _get_usernames_map(db, user_ids)

    active_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), usernames_map, now_local) for task in active_tasks],
        key=lambda item: (
            -_priority_weight(item.priority),
            item.due_time or time.max,
            item.created_at,
        ),
    )
    overdue_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), usernames_map, now_local) for task in overdue_tasks],
        key=lambda item: (
            -((today - item.due_date).days if item.due_date else -1),
            -_priority_weight(item.priority),
            item.created_at,
        ),
    )
    done_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), usernames_map, now_local) for task in done_tasks],
        key=lambda item: item.verified_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return [*active_sorted, *overdue_sorted, *done_sorted]


def create_task(db: Session, current_user_id: int, payload: TaskCreatePayload) -> TaskDto:
    assignee_ids = sorted(set(payload.assignee_user_ids)) or [current_user_id]

    task = Task(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        due_time=payload.due_time,
        status="active",
        priority=payload.priority,
        verifier_user_id=payload.verifier_user_id,
        created_by_user_id=current_user_id,
        created_at=_now(),
        source_type=payload.source_type,
        source_id=payload.source_id,
        is_recurring=payload.is_recurring,
        recurrence_type=payload.recurrence_type,
        recurrence_interval=payload.recurrence_interval,
        recurrence_days_of_week=payload.recurrence_days_of_week,
        recurrence_end_date=payload.recurrence_end_date,
        recurrence_state="active",
        is_hidden=False,
    )
    db.add(task)
    for user_id in assignee_ids:
        db.add(TaskAssignee(task_id=task.id, user_id=user_id))

    db.flush()
    _generate_recurrence_children(db, task, assignee_ids)

    db.commit()
    return get_task_dto(db, task.id, current_user_id)


def get_task(db: Session, task_id: str) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id))


def _resolve_master_task(db: Session, task: Task) -> Task:
    if not task.recurrence_master_task_id:
        return task

    master_task = get_task(db, task.recurrence_master_task_id)
    return master_task or task


def is_user_task_editor(db: Session, task_id: str, user_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    if task.created_by_user_id == user_id:
        return True
    if user_can_manage_access(db, user_id):
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
    user_ids = [task.created_by_user_id, *assignee_ids]
    if task.verifier_user_id:
        user_ids.append(task.verifier_user_id)
    return _to_dto(task, assignee_ids, _get_usernames_map(db, user_ids), _now_local())


def update_task(db: Session, task_id: str, payload: TaskUpdatePayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    updates = payload.model_dump(exclude_unset=True)
    for field in ["title", "description", "priority", "status", "verifier_user_id", "due_date", "due_time"]:
        if field in updates:
            setattr(task, field, updates[field])

    if "status" in updates and updates["status"] == DONE_STATUS:
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

    is_admin = user_can_manage_access(db, current_user_id)
    is_assignee = (
        db.scalar(
            select(TaskAssignee.task_id)
            .where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == current_user_id)
            .limit(1)
        )
        is not None
    )
    is_creator = task.created_by_user_id == current_user_id
    if not (is_creator or is_assignee or is_admin):
        raise ValueError("forbidden")
    if task.status != "active":
        raise ValueError("complete_only_active")

    now = _now()
    task.completed_at = now

    if is_creator or is_admin:
        task.status = DONE_STATUS
        task.verified_at = now
    else:
        task.status = "done_pending_verify"

    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def verify_task(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if not (user_can_manage_access(db, current_user_id) or task.created_by_user_id == current_user_id):
        raise ValueError("forbidden")

    task.status = DONE_STATUS
    task.verified_at = _now()
    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def delete_task(db: Session, task_id: str, current_user_id: int) -> None:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    if task.status == DONE_STATUS:
        raise ValueError("done_delete_forbidden")
    if task.status != "active":
        raise ValueError("delete_only_active")

    if not is_user_task_editor(db, task_id, current_user_id):
        raise ValueError("forbidden")

    db.delete(task)
    db.commit()


def get_task_badges(db: Session, current_user_id: int) -> TaskBadgesDto:
    is_admin = user_can_manage_access(db, current_user_id)
    verify_query = select(func.count(Task.id)).where(
        Task.status == "done_pending_verify",
        Task.is_hidden.is_(False),
    )
    if not is_admin:
        verify_query = verify_query.where(Task.created_by_user_id == current_user_id)

    pending_verify_count = db.scalar(verify_query) or 0
    return TaskBadgesDto(
        pending_verify_count=pending_verify_count,
        fresh_completed_flag=pending_verify_count > 0,
    )


def apply_recurrence_action(
    db: Session,
    task_id: str,
    payload: RecurrenceActionPayload,
    current_user_id: int,
) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")

    master_task = _resolve_master_task(db, task)
    if not master_task.is_recurring:
        raise ValueError("recurrence_not_supported")

    today = _now().date()

    if payload.action == "pause":
        master_task.recurrence_state = "paused"
        db.query(Task).filter(
            Task.recurrence_master_task_id == master_task.id,
            Task.due_date >= today,
        ).update({Task.is_hidden: True}, synchronize_session=False)
    elif payload.action == "resume":
        master_task.recurrence_state = "active"
        db.query(Task).filter(
            Task.recurrence_master_task_id == master_task.id,
            Task.due_date >= today,
        ).update({Task.is_hidden: False}, synchronize_session=False)
    elif payload.action == "stop":
        master_task.recurrence_state = "stopped"
        db.execute(
            delete(Task).where(
                Task.recurrence_master_task_id == master_task.id,
                Task.due_date >= today,
            )
        )

    db.commit()
    return get_task_dto(db, master_task.id, current_user_id)
