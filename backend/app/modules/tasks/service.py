from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.admin_access.service import user_can_manage_access
from app.modules.auth.models import User
from app.modules.tasks.models import Task, TaskAssignee, TaskVerifier
from app.modules.tasks.schemas import (
    CalendarDayDto,
    RecurrenceActionPayload,
    TaskBadgeDto,
    TaskCreatePayload,
    TaskDto,
    TaskUpdatePayload,
    TaskUserDto,
)

DONE_STATUS = "done"
ACTIVE_STATUS = "active"
PENDING_VERIFY_STATUS = "done_pending_verify"


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

    month_index = current.month - 1 + recurrence_interval
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, monthrange(year, month)[1])
    return date(year, month, day)


def _get_linked_user_ids_map(db: Session, task_ids: list[str], model: type[TaskAssignee] | type[TaskVerifier]) -> dict[str, list[int]]:
    if not task_ids:
        return {}
    rows = db.execute(select(model.task_id, model.user_id).where(model.task_id.in_(task_ids))).all()
    ret: dict[str, list[int]] = {task_id: [] for task_id in task_ids}
    for task_id, user_id in rows:
        ret.setdefault(task_id, []).append(user_id)
    return ret


def _is_overdue(task: Task, now_local: datetime) -> bool:
    if task.status == DONE_STATUS or task.is_hidden or not task.due_date:
        return False
    today = now_local.date()
    if task.due_date < today:
        return True
    if task.due_date > today or task.due_time is None:
        return False
    return task.due_time < now_local.time().replace(tzinfo=None)


def _to_dto(task: Task, assignee_ids: list[int], verifier_ids: list[int], now_local: datetime) -> TaskDto:
    return TaskDto(
        id=task.id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        due_time=task.due_time,
        status=task.status,
        priority=task.priority,
        verifier_user_ids=verifier_ids,
        created_by_user_id=task.created_by_user_id,
        created_at=task.created_at,
        completed_at=task.completed_at,
        verified_at=task.verified_at,
        source_type=task.source_type,
        source_id=task.source_id,
        assignee_user_ids=assignee_ids,
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


def _build_tab_filter(current_user_id: int, tab: str):
    if tab == "verify":
        return exists(select(TaskVerifier.task_id).where(TaskVerifier.task_id == Task.id, TaskVerifier.user_id == current_user_id))
    if tab == "created":
        return Task.created_by_user_id == current_user_id
    return exists(select(TaskAssignee.task_id).where(TaskAssignee.task_id == Task.id, TaskAssignee.user_id == current_user_id))


def _assert_active(task: Task) -> None:
    if task.status != ACTIVE_STATUS:
        raise ValueError("status_must_be_active")


def _can_edit_or_delete(db: Session, task: Task, user_id: int) -> bool:
    return task.created_by_user_id == user_id or user_can_manage_access(db, user_id)


def _generate_recurrence_children(db: Session, master_task: Task, assignee_ids: list[int], verifier_ids: list[int]) -> None:
    if not master_task.is_recurring or not master_task.due_date or not master_task.recurrence_type:
        return

    interval = master_task.recurrence_interval or 1
    current_date = master_task.due_date
    for _ in range(365):
        current_date = _advance_date(current_date, master_task.recurrence_type, interval)
        if master_task.recurrence_end_date and current_date > master_task.recurrence_end_date:
            break

        child = Task(
            id=str(uuid4()),
            title=master_task.title,
            description=master_task.description,
            due_date=current_date,
            due_time=master_task.due_time,
            status=ACTIVE_STATUS,
            priority=master_task.priority,
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
        for verifier_id in verifier_ids:
            db.add(TaskVerifier(task_id=child.id, user_id=verifier_id))


def list_users(db: Session) -> list[TaskUserDto]:
    users = db.scalars(select(User).order_by(User.username)).all()
    return [TaskUserDto(id=user.id, username=user.username) for user in users]


def list_calendar_days(db: Session, current_user_id: int, from_date: date, to_date: date, tab: str) -> list[CalendarDayDto]:
    today = _now_local().date()
    query = (
        select(Task.due_date, func.count(Task.id))
        .where(
            Task.due_date.is_not(None),
            Task.due_date >= from_date,
            Task.due_date <= to_date,
            Task.due_date >= today,
            Task.status != DONE_STATUS,
            Task.is_hidden.is_(False),
            _build_tab_filter(current_user_id, tab),
        )
        .group_by(Task.due_date)
        .order_by(Task.due_date)
    )
    rows = db.execute(query).all()
    return [CalendarDayDto(date=row[0], count=row[1]) for row in rows]


def list_tasks_for_date(db: Session, current_user_id: int, selected_date: date, tab: str) -> list[TaskDto]:
    now_local = _now_local()
    today = now_local.date()
    now_time = now_local.time().replace(tzinfo=None)
    tab_filter = _build_tab_filter(current_user_id, tab)

    overdue_query = select(Task).where(
        Task.status.in_([ACTIVE_STATUS, PENDING_VERIFY_STATUS]),
        Task.is_hidden.is_(False),
        tab_filter,
        or_(
            Task.due_date < today,
            and_(Task.due_date == today, Task.due_time.is_not(None), Task.due_time < now_time),
        ),
    )
    active_query = select(Task).where(
        Task.due_date == selected_date,
        Task.status.in_([ACTIVE_STATUS, PENDING_VERIFY_STATUS]),
        Task.is_hidden.is_(False),
        tab_filter,
    )
    done_query = select(Task).where(
        Task.due_date == selected_date,
        Task.status == DONE_STATUS,
        Task.is_hidden.is_(False),
        tab_filter,
    )

    overdue_tasks = list(db.scalars(overdue_query))
    overdue_ids = {task.id for task in overdue_tasks}
    active_tasks = [task for task in db.scalars(active_query) if task.id not in overdue_ids]
    done_tasks = list(db.scalars(done_query))
    all_tasks = active_tasks + overdue_tasks + done_tasks
    assignee_map = _get_linked_user_ids_map(db, [task.id for task in all_tasks], TaskAssignee)
    verifier_map = _get_linked_user_ids_map(db, [task.id for task in all_tasks], TaskVerifier)

    active_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), verifier_map.get(task.id, []), now_local) for task in active_tasks],
        key=lambda item: (-_priority_weight(item.priority), item.due_time or time.max, item.created_at),
    )
    overdue_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), verifier_map.get(task.id, []), now_local) for task in overdue_tasks],
        key=lambda item: (-((today - item.due_date).days if item.due_date else -1), -_priority_weight(item.priority), item.created_at),
    )
    done_sorted = sorted(
        [_to_dto(task, assignee_map.get(task.id, []), verifier_map.get(task.id, []), now_local) for task in done_tasks],
        key=lambda item: item.verified_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return [*active_sorted, *overdue_sorted, *done_sorted]


def get_task_badges(db: Session, current_user_id: int) -> TaskBadgeDto:
    base_filter = exists(select(TaskVerifier.task_id).where(TaskVerifier.task_id == Task.id, TaskVerifier.user_id == current_user_id))
    pending = db.scalar(select(func.count(Task.id)).where(Task.status == PENDING_VERIFY_STATUS, Task.is_hidden.is_(False), base_filter)) or 0
    fresh_completed = (
        db.scalar(
            select(func.count(Task.id)).where(
                Task.status == PENDING_VERIFY_STATUS,
                Task.completed_at.is_not(None),
                Task.is_hidden.is_(False),
                base_filter,
            )
        )
        or 0
    )
    return TaskBadgeDto(pending_verify_count=pending, fresh_completed_count=fresh_completed)


def create_task(db: Session, current_user_id: int, payload: TaskCreatePayload) -> TaskDto:
    task = Task(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        due_time=payload.due_time,
        status=ACTIVE_STATUS,
        priority=payload.priority,
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
    assignee_ids = sorted({user_id for user_id in payload.assignee_user_ids if user_id > 0})
    if not assignee_ids:
        assignee_ids = [current_user_id]
    verifier_ids = sorted({user_id for user_id in payload.verifier_user_ids if user_id > 0})
    for user_id in assignee_ids:
        db.add(TaskAssignee(task_id=task.id, user_id=user_id))
    for user_id in verifier_ids:
        db.add(TaskVerifier(task_id=task.id, user_id=user_id))

    db.flush()
    _generate_recurrence_children(db, task, assignee_ids, verifier_ids)
    db.commit()
    return get_task_dto(db, task.id, current_user_id)


def get_task(db: Session, task_id: str) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id))


def get_task_dto(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    assignee_ids = _get_linked_user_ids_map(db, [task.id], TaskAssignee).get(task.id, [])
    verifier_ids = _get_linked_user_ids_map(db, [task.id], TaskVerifier).get(task.id, [])
    return _to_dto(task, assignee_ids, verifier_ids, _now_local())


def is_user_task_viewer(db: Session, task_id: str, user_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    if user_can_manage_access(db, user_id) or task.created_by_user_id == user_id:
        return True
    is_assignee = db.scalar(select(TaskAssignee).where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id).limit(1))
    is_verifier = db.scalar(select(TaskVerifier).where(TaskVerifier.task_id == task_id, TaskVerifier.user_id == user_id).limit(1))
    return is_assignee is not None or is_verifier is not None


def update_task(db: Session, task_id: str, payload: TaskUpdatePayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if task.is_recurring and not task.recurrence_master_task_id:
        raise ValueError("master_task_edit_forbidden")
    if not _can_edit_or_delete(db, task, current_user_id):
        raise ValueError("forbidden")
    _assert_active(task)

    updates = payload.model_dump(exclude_unset=True)
    for field in ["title", "description", "priority", "due_date", "due_time"]:
        if field in updates:
            setattr(task, field, updates[field])

    if payload.assignee_user_ids is not None:
        db.query(TaskAssignee).filter(TaskAssignee.task_id == task_id).delete()
        for user_id in sorted({user_id for user_id in payload.assignee_user_ids if user_id > 0}):
            db.add(TaskAssignee(task_id=task_id, user_id=user_id))
    if payload.verifier_user_ids is not None:
        db.query(TaskVerifier).filter(TaskVerifier.task_id == task_id).delete()
        for user_id in sorted({user_id for user_id in payload.verifier_user_ids if user_id > 0}):
            db.add(TaskVerifier(task_id=task_id, user_id=user_id))

    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def return_task_to_active(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if not _can_edit_or_delete(db, task, current_user_id):
        raise ValueError("forbidden")
    if task.status not in (DONE_STATUS, PENDING_VERIFY_STATUS):
        raise ValueError("invalid_status_transition")

    task.status = ACTIVE_STATUS
    task.completed_at = None
    task.verified_at = None
    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def complete_task(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if task.status != ACTIVE_STATUS:
        raise ValueError("invalid_status_transition")

    is_admin = user_can_manage_access(db, current_user_id)
    is_assignee = db.scalar(select(TaskAssignee.task_id).where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == current_user_id).limit(1)) is not None
    is_creator = task.created_by_user_id == current_user_id
    if not (is_creator or is_assignee or is_admin):
        raise ValueError("forbidden")

    verifier_ids = _get_linked_user_ids_map(db, [task_id], TaskVerifier).get(task_id, [])
    now = _now()
    task.completed_at = now
    task.verified_at = now if not verifier_ids else None
    task.status = DONE_STATUS if not verifier_ids else PENDING_VERIFY_STATUS

    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def verify_task(db: Session, task_id: str, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if task.status != PENDING_VERIFY_STATUS:
        raise ValueError("invalid_status_transition")

    is_verifier = db.scalar(select(TaskVerifier.task_id).where(TaskVerifier.task_id == task_id, TaskVerifier.user_id == current_user_id).limit(1)) is not None
    if not is_verifier:
        raise ValueError("forbidden")

    task.status = DONE_STATUS
    task.verified_at = _now()
    db.commit()
    return get_task_dto(db, task_id, current_user_id)


def delete_task(db: Session, task_id: str, current_user_id: int) -> None:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    if not _can_edit_or_delete(db, task, current_user_id):
        raise ValueError("forbidden")
    _assert_active(task)

    if task.is_recurring and not task.recurrence_master_task_id:
        has_children = db.scalar(select(func.count(Task.id)).where(Task.recurrence_master_task_id == task.id)) or 0
        if has_children:
            raise ValueError("master_has_children")

    db.delete(task)
    db.commit()


def delete_recurrence_children(
    db: Session,
    task_id: str,
    current_user_id: int,
    mode: str,
    pivot_date: date | None,
) -> int:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    master_id = task.id if task.is_recurring and not task.recurrence_master_task_id else task.recurrence_master_task_id
    if not master_id:
        raise ValueError("recurrence_not_supported")

    master = get_task(db, master_id)
    if not master or not _can_edit_or_delete(db, master, current_user_id):
        raise ValueError("forbidden")

    filters = [Task.recurrence_master_task_id == master_id, Task.status != DONE_STATUS]
    if mode == "before" and pivot_date:
        filters.append(Task.due_date <= pivot_date)
    elif mode == "after" and pivot_date:
        filters.append(Task.due_date >= pivot_date)

    deleted = db.query(Task).filter(*filters).delete(synchronize_session=False)
    db.commit()
    return deleted


def apply_recurrence_action(db: Session, task_id: str, payload: RecurrenceActionPayload, current_user_id: int) -> TaskDto:
    task = get_task(db, task_id)
    if not task:
        raise ValueError("task_not_found")
    master_task = task if task.is_recurring and not task.recurrence_master_task_id else get_task(db, task.recurrence_master_task_id or "")
    if not master_task or not master_task.is_recurring:
        raise ValueError("recurrence_not_supported")
    if not _can_edit_or_delete(db, master_task, current_user_id):
        raise ValueError("forbidden")

    today = _now().date()
    if payload.action == "pause":
        master_task.recurrence_state = "paused"
        db.query(Task).filter(Task.recurrence_master_task_id == master_task.id, Task.due_date >= today).update({Task.is_hidden: True}, synchronize_session=False)
    elif payload.action == "resume":
        master_task.recurrence_state = "active"
        db.query(Task).filter(Task.recurrence_master_task_id == master_task.id, Task.due_date >= today).update({Task.is_hidden: False}, synchronize_session=False)
    elif payload.action == "stop":
        master_task.recurrence_state = "stopped"
        db.execute(delete(Task).where(Task.recurrence_master_task_id == master_task.id, Task.due_date >= today, Task.status != DONE_STATUS))

    db.commit()
    return get_task_dto(db, master_task.id, current_user_id)
