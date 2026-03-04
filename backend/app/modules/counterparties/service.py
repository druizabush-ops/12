from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.counterparties.models import (
    Counterparty,
    CounterpartyAutoTaskBinding,
    CounterpartyAutoTaskRule,
    CounterpartyFolder,
)
from app.modules.counterparties.schemas import (
    AutoTaskPrimaryPayload,
    AutoTaskReviewPayload,
    AutoTaskSchedulePayload,
    CounterpartyAutoTaskBindingDto,
    CounterpartyAutoTaskRuleDto,
    CounterpartyAutoTaskRuleUpsertPayload,
    CounterpartyDto,
    CounterpartyFolderCreatePayload,
    CounterpartyFolderDto,
    CounterpartyFolderUpdatePayload,
    CounterpartyUpsertPayload,
)
from app.modules.tasks.schemas import TaskCreatePayload
from app.modules.tasks.service import create_task, delete_task


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_days(days: list[int]) -> str | None:
    if not days:
        return None
    unique_days = sorted({day for day in days if day in {1, 2, 3, 4, 5, 6, 7}})
    return ",".join(str(day) for day in unique_days) or None


def _deserialize_days(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(value) for value in raw.split(",") if value]


def _folder_to_dto(folder: CounterpartyFolder) -> CounterpartyFolderDto:
    return CounterpartyFolderDto(
        id=folder.id,
        parent_id=folder.parent_id,
        name=folder.name,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


def _counterparty_to_dto(item: Counterparty) -> CounterpartyDto:
    return CounterpartyDto(
        id=item.id,
        folder_id=item.folder_id,
        group_id=item.group_id,
        is_archived=item.is_archived,
        status=item.status,
        sort_order=item.sort_order,
        name=item.name,
        legal_name=item.legal_name,
        city=item.city,
        product_group=item.product_group,
        department=item.department,
        website=item.website,
        login=item.login,
        password=item.password,
        messenger=item.messenger,
        phone=item.phone,
        email=item.email,
        order_day_of_week=item.order_day_of_week,
        order_deadline_time=item.order_deadline_time,
        delivery_day_of_week=item.delivery_day_of_week,
        defect_notes=item.defect_notes,
        inn=item.inn,
        kpp=item.kpp,
        ogrn=item.ogrn,
        legal_address=item.legal_address,
        bank_name=item.bank_name,
        bank_bik=item.bank_bik,
        account=item.account,
        corr_account=item.corr_account,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def list_folders(db: Session) -> list[CounterpartyFolderDto]:
    items = db.scalars(select(CounterpartyFolder).order_by(CounterpartyFolder.sort_order, CounterpartyFolder.id)).all()
    return [_folder_to_dto(item) for item in items]


def create_folder(db: Session, payload: CounterpartyFolderCreatePayload) -> CounterpartyFolderDto:
    now = _now()
    folder = CounterpartyFolder(
        parent_id=payload.parent_id,
        name=payload.name,
        sort_order=payload.sort_order,
        created_at=now,
        updated_at=now,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return _folder_to_dto(folder)


def update_folder(db: Session, folder_id: int, payload: CounterpartyFolderUpdatePayload) -> CounterpartyFolderDto:
    folder = db.get(CounterpartyFolder, folder_id)
    if folder is None:
        raise ValueError("folder_not_found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(folder, field, value)
    folder.updated_at = _now()
    db.commit()
    db.refresh(folder)
    return _folder_to_dto(folder)


def list_counterparties(db: Session, include_archived: bool) -> list[CounterpartyDto]:
    query = select(Counterparty)
    if not include_archived:
        query = query.where(Counterparty.is_archived.is_(False))
    items = db.scalars(query.order_by(Counterparty.sort_order, Counterparty.id)).all()
    return [_counterparty_to_dto(item) for item in items]


def get_counterparty_dto(db: Session, counterparty_id: int) -> CounterpartyDto:
    item = db.get(Counterparty, counterparty_id)
    if item is None:
        raise ValueError("counterparty_not_found")
    return _counterparty_to_dto(item)


def create_counterparty(db: Session, payload: CounterpartyUpsertPayload) -> CounterpartyDto:
    now = _now()
    item = Counterparty(**payload.model_dump(), created_at=now, updated_at=now)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _counterparty_to_dto(item)


def update_counterparty(db: Session, counterparty_id: int, payload: CounterpartyUpsertPayload) -> CounterpartyDto:
    item = db.get(Counterparty, counterparty_id)
    if item is None:
        raise ValueError("counterparty_not_found")

    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    item.updated_at = _now()
    db.flush()

    if item.is_archived or item.status == "inactive":
        rules = db.scalars(
            select(CounterpartyAutoTaskRule).where(CounterpartyAutoTaskRule.counterparty_id == counterparty_id)
        ).all()
        for rule in rules:
            rule.is_enabled = False
            rule.updated_at = _now()

    db.commit()
    db.refresh(item)
    return _counterparty_to_dto(item)


def archive_counterparty(db: Session, counterparty_id: int, archived: bool) -> CounterpartyDto:
    item = db.get(Counterparty, counterparty_id)
    if item is None:
        raise ValueError("counterparty_not_found")
    item.is_archived = archived
    item.updated_at = _now()

    if archived:
        rules = db.scalars(
            select(CounterpartyAutoTaskRule).where(CounterpartyAutoTaskRule.counterparty_id == counterparty_id)
        ).all()
        for rule in rules:
            rule.is_enabled = False
            rule.updated_at = _now()

    db.commit()
    db.refresh(item)
    return _counterparty_to_dto(item)


def _create_recurring_master_task(
    db: Session,
    current_user_id: int,
    counterparty_id: int,
    rule_id: int,
    schedule: AutoTaskSchedulePayload,
    primary: AutoTaskPrimaryPayload | AutoTaskReviewPayload,
) -> str:
    task = create_task(
        db,
        current_user_id,
        TaskCreatePayload(
            title=primary.text or "",
            due_date=_now().date(),
            due_time=primary.due_time,
            assignee_user_ids=[primary.assignee_user_id] if primary.assignee_user_id else [],
            is_recurring=True,
            recurrence_type=schedule.recurrence_type,
            recurrence_interval=schedule.recurrence_interval,
            recurrence_days_of_week=_serialize_days(schedule.recurrence_days_of_week),
            recurrence_end_date=schedule.recurrence_end_date,
            source_type="counterparty_rule",
            source_id=f"counterparty:{counterparty_id}:rule:{rule_id}",
            source_module="counterparties",
            source_counterparty_id=counterparty_id,
            source_trigger_id=rule_id,
        ),
    )
    return task.id


def _delete_series(db: Session, current_user_id: int, master_id: str | None) -> None:
    if not master_id:
        return

    from app.modules.tasks.models import Task

    items = db.scalars(select(Task.id).where(Task.recurrence_master_task_id == master_id)).all()
    for task_id in items:
        delete_task(db, task_id, current_user_id)
    delete_task(db, master_id, current_user_id)


def _rule_to_dto(rule: CounterpartyAutoTaskRule, binding: CounterpartyAutoTaskBinding | None) -> CounterpartyAutoTaskRuleDto:
    return CounterpartyAutoTaskRuleDto(
        id=rule.id,
        counterparty_id=rule.counterparty_id,
        is_enabled=rule.is_enabled,
        title=rule.title,
        kind=rule.kind,
        schedule=AutoTaskSchedulePayload(
            recurrence_type=rule.recurrence_type,
            recurrence_interval=rule.recurrence_interval,
            recurrence_days_of_week=_deserialize_days(rule.recurrence_days_of_week),
            recurrence_end_date=rule.recurrence_end_date,
        ),
        primary_task=AutoTaskPrimaryPayload(
            assignee_user_id=rule.primary_assignee_user_id,
            text=rule.primary_text,
            due_time=rule.primary_due_time,
        ),
        review_task=AutoTaskReviewPayload(
            enabled=rule.review_enabled,
            assignee_user_id=rule.review_assignee_user_id,
            text=rule.review_text,
            due_time=rule.review_due_time,
        ),
        binding=(
            CounterpartyAutoTaskBindingDto(
                primary_master_task_id=binding.primary_master_task_id,
                review_master_task_id=binding.review_master_task_id,
            )
            if binding
            else None
        ),
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def list_auto_task_rules(db: Session, counterparty_id: int) -> list[CounterpartyAutoTaskRuleDto]:
    rules = db.scalars(
        select(CounterpartyAutoTaskRule)
        .where(CounterpartyAutoTaskRule.counterparty_id == counterparty_id)
        .order_by(CounterpartyAutoTaskRule.id.desc())
    ).all()
    ret: list[CounterpartyAutoTaskRuleDto] = []
    for rule in rules:
        binding = db.scalar(
            select(CounterpartyAutoTaskBinding).where(CounterpartyAutoTaskBinding.rule_id == rule.id)
        )
        ret.append(_rule_to_dto(rule, binding))
    return ret


def create_auto_task_rule(
    db: Session,
    current_user_id: int,
    counterparty_id: int,
    payload: CounterpartyAutoTaskRuleUpsertPayload,
) -> CounterpartyAutoTaskRuleDto:
    counterparty = db.get(Counterparty, counterparty_id)
    if counterparty is None:
        raise ValueError("counterparty_not_found")

    is_enabled = payload.is_enabled and (not counterparty.is_archived and counterparty.status == "active")
    now = _now()
    rule = CounterpartyAutoTaskRule(
        counterparty_id=counterparty_id,
        is_enabled=is_enabled,
        title=payload.title,
        kind=payload.kind,
        recurrence_type=payload.schedule.recurrence_type,
        recurrence_interval=payload.schedule.recurrence_interval,
        recurrence_days_of_week=_serialize_days(payload.schedule.recurrence_days_of_week),
        recurrence_end_date=payload.schedule.recurrence_end_date,
        primary_assignee_user_id=payload.primary_task.assignee_user_id,
        primary_text=payload.primary_task.text,
        primary_due_time=payload.primary_task.due_time,
        review_enabled=payload.review_task.enabled,
        review_assignee_user_id=payload.review_task.assignee_user_id,
        review_text=payload.review_task.text,
        review_due_time=payload.review_task.due_time,
        created_at=now,
        updated_at=now,
    )
    db.add(rule)
    db.flush()

    binding: CounterpartyAutoTaskBinding | None = None
    if is_enabled:
        primary_master_task_id = _create_recurring_master_task(
            db,
            current_user_id,
            counterparty_id,
            rule.id,
            payload.schedule,
            payload.primary_task,
        )
        review_master_task_id: str | None = None
        if payload.review_task.enabled:
            review_master_task_id = _create_recurring_master_task(
                db,
                current_user_id,
                counterparty_id,
                rule.id,
                payload.schedule,
                payload.review_task,
            )
        binding = CounterpartyAutoTaskBinding(
            rule_id=rule.id,
            primary_master_task_id=primary_master_task_id,
            review_master_task_id=review_master_task_id,
            created_at=now,
            updated_at=now,
        )
        db.add(binding)

    db.commit()
    db.refresh(rule)
    if binding:
        db.refresh(binding)
    return _rule_to_dto(rule, binding)


def update_auto_task_rule(
    db: Session,
    current_user_id: int,
    counterparty_id: int,
    rule_id: int,
    payload: CounterpartyAutoTaskRuleUpsertPayload,
) -> CounterpartyAutoTaskRuleDto:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id:
        raise ValueError("rule_not_found")
    counterparty = db.get(Counterparty, counterparty_id)
    if counterparty is None:
        raise ValueError("counterparty_not_found")

    binding = db.scalar(select(CounterpartyAutoTaskBinding).where(CounterpartyAutoTaskBinding.rule_id == rule_id))
    has_existing_series = binding is not None
    if has_existing_series and payload.update_mode is None:
        raise ValueError("update_mode_required")

    if has_existing_series and payload.update_mode == "replace_existing":
        _delete_series(db, current_user_id, binding.primary_master_task_id)
        _delete_series(db, current_user_id, binding.review_master_task_id)
        db.delete(binding)
        db.flush()
        binding = None

    rule.title = payload.title
    rule.kind = payload.kind
    rule.recurrence_type = payload.schedule.recurrence_type
    rule.recurrence_interval = payload.schedule.recurrence_interval
    rule.recurrence_days_of_week = _serialize_days(payload.schedule.recurrence_days_of_week)
    rule.recurrence_end_date = payload.schedule.recurrence_end_date
    rule.primary_assignee_user_id = payload.primary_task.assignee_user_id
    rule.primary_text = payload.primary_task.text
    rule.primary_due_time = payload.primary_task.due_time
    rule.review_enabled = payload.review_task.enabled
    rule.review_assignee_user_id = payload.review_task.assignee_user_id
    rule.review_text = payload.review_task.text
    rule.review_due_time = payload.review_task.due_time

    effective_enabled = payload.is_enabled and not counterparty.is_archived and counterparty.status == "active"
    rule.is_enabled = effective_enabled
    rule.updated_at = _now()

    if effective_enabled and (binding is None or payload.update_mode in {"keep_existing", "replace_existing"}):
        primary_master_task_id = _create_recurring_master_task(
            db,
            current_user_id,
            counterparty_id,
            rule.id,
            payload.schedule,
            payload.primary_task,
        )
        review_master_task_id: str | None = None
        if payload.review_task.enabled:
            review_master_task_id = _create_recurring_master_task(
                db,
                current_user_id,
                counterparty_id,
                rule.id,
                payload.schedule,
                payload.review_task,
            )
        if binding is None:
            binding = CounterpartyAutoTaskBinding(
                rule_id=rule.id,
                primary_master_task_id=primary_master_task_id,
                review_master_task_id=review_master_task_id,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(binding)
        else:
            binding.primary_master_task_id = primary_master_task_id
            binding.review_master_task_id = review_master_task_id
            binding.updated_at = _now()

    db.commit()
    db.refresh(rule)
    if binding:
        db.refresh(binding)
    return _rule_to_dto(rule, binding)
