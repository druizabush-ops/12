from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.counterparties.models import (
    Counterparty,
    CounterpartyAutoTaskRule,
    CounterpartyAutoTaskRuleAssignee,
    CounterpartyAutoTaskRuleVerifier,
    CounterpartyFolder,
    CounterpartyModuleSettings,
)
from app.modules.counterparties.schemas import (
    CounterpartyAutoTaskRuleCreatePayload,
    CounterpartyAutoTaskRuleDto,
    CounterpartyAutoTaskRulePatchPayload,
    CounterpartyDto,
    CounterpartyFolderCreatePayload,
    CounterpartyFolderDto,
    CounterpartyFolderUpdatePayload,
    CounterpartyTaskCreatorSettingsDto,
    CounterpartyTaskCreatorSettingsPayload,
    CounterpartyUpsertPayload,
)
from app.modules.tasks.models import Task, TaskAssignee, TaskVerifier


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _render_template(template: str | None, counterparty: Counterparty) -> str | None:
    if template is None:
        return None
    return template.replace("{counterparty_name}", counterparty.name)


def _weekday_dates(start: date, horizon_days: int, weekday: int) -> list[date]:
    ret: list[date] = []
    for offset in range(horizon_days + 1):
        day = start + timedelta(days=offset)
        if day.isoweekday() == weekday:
            ret.append(day)
    return ret


def _folder_to_dto(folder: CounterpartyFolder) -> CounterpartyFolderDto:
    return CounterpartyFolderDto.model_validate(folder, from_attributes=True)


def _counterparty_to_dto(item: Counterparty) -> CounterpartyDto:
    return CounterpartyDto.model_validate(item, from_attributes=True)


def _rule_to_dto(db: Session, rule: CounterpartyAutoTaskRule, effective_state: str | None = None) -> CounterpartyAutoTaskRuleDto:
    assignee_ids = [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleAssignee.user_id).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id)).all()]
    verifier_ids = [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleVerifier.user_id).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id)).all()]
    return CounterpartyAutoTaskRuleDto(
        id=rule.id,
        counterparty_id=rule.counterparty_id,
        task_kind=rule.task_kind,
        title_template=rule.title_template,
        description_template=rule.description_template,
        assignee_user_ids=assignee_ids,
        verifier_user_ids=verifier_ids or None,
        is_enabled=rule.is_enabled,
        schedule_weekday=rule.schedule_weekday,
        schedule_due_time=rule.schedule_due_time,
        horizon_days=rule.horizon_days,
        linked_task_master_id=rule.linked_task_master_id,
        state=effective_state or rule.state,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _get_settings(db: Session) -> CounterpartyModuleSettings:
    settings = db.scalar(select(CounterpartyModuleSettings).order_by(CounterpartyModuleSettings.id.asc()).limit(1))
    if settings:
        return settings
    settings = CounterpartyModuleSettings(task_creator_user_id=None, updated_at=_now())
    db.add(settings)
    db.flush()
    return settings


def _create_master_task(db: Session, counterparty: Counterparty, rule: CounterpartyAutoTaskRule, creator_user_id: int) -> Task:
    task = Task(
        id=str(uuid4()),
        title=_render_template(rule.title_template, counterparty) or "",
        description=_render_template(rule.description_template, counterparty),
        due_date=None,
        due_time=rule.schedule_due_time,
        status="active",
        priority=None,
        created_by_user_id=creator_user_id,
        created_at=_now(),
        source_type="counterparty_auto_task_rule",
        source_id=f"counterparty:{counterparty.id}:rule:{rule.id}",
        source_module="counterparties",
        source_counterparty_id=counterparty.id,
        source_trigger_id=rule.id,
        is_recurring=True,
        recurrence_type="weekly",
        recurrence_interval=1,
        recurrence_days_of_week=str(rule.schedule_weekday),
        recurrence_end_date=None,
        recurrence_master_task_id=None,
        recurrence_state="active",
        is_hidden=False,
    )
    db.add(task)
    db.flush()
    return task


def _replace_task_links(db: Session, task_id: str, assignee_ids: list[int], verifier_ids: list[int]) -> None:
    db.execute(delete(TaskAssignee).where(TaskAssignee.task_id == task_id))
    db.execute(delete(TaskVerifier).where(TaskVerifier.task_id == task_id))
    for user_id in sorted({uid for uid in assignee_ids if uid > 0}):
        db.add(TaskAssignee(task_id=task_id, user_id=user_id))
    for user_id in sorted({uid for uid in verifier_ids if uid > 0}):
        db.add(TaskVerifier(task_id=task_id, user_id=user_id))


def ensure_horizon(db: Session, rule: CounterpartyAutoTaskRule, today: date | None = None) -> None:
    counterparty = db.get(Counterparty, rule.counterparty_id)
    if not counterparty or counterparty.is_archived or rule.state != "active" or not rule.is_enabled or not rule.linked_task_master_id:
        return
    today_value = today or _now().date()
    due_dates = _weekday_dates(today_value, rule.horizon_days, rule.schedule_weekday)
    existing = {
        row[0]
        for row in db.execute(
            select(Task.due_date).where(
                Task.source_trigger_id == rule.id,
                Task.recurrence_master_task_id == rule.linked_task_master_id,
                Task.due_date >= today_value,
                Task.due_date <= today_value + timedelta(days=rule.horizon_days),
            )
        ).all()
        if row[0] is not None
    }
    assignee_ids = [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleAssignee.user_id).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id)).all()]
    verifier_ids = [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleVerifier.user_id).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id)).all()]
    master = db.get(Task, rule.linked_task_master_id)
    if not master:
        return

    for due in due_dates:
        if due in existing:
            continue
        child = Task(
            id=str(uuid4()),
            title=_render_template(rule.title_template, counterparty) or "",
            description=_render_template(rule.description_template, counterparty),
            due_date=due,
            due_time=rule.schedule_due_time,
            status="active",
            priority=None,
            created_by_user_id=master.created_by_user_id,
            created_at=_now(),
            source_type=master.source_type,
            source_id=master.source_id,
            source_module="counterparties",
            source_counterparty_id=counterparty.id,
            source_trigger_id=rule.id,
            is_recurring=True,
            recurrence_type=master.recurrence_type,
            recurrence_interval=master.recurrence_interval,
            recurrence_days_of_week=master.recurrence_days_of_week,
            recurrence_end_date=master.recurrence_end_date,
            recurrence_master_task_id=master.id,
            recurrence_state=master.recurrence_state,
            is_hidden=False,
        )
        db.add(child)
        db.flush()
        _replace_task_links(db, child.id, assignee_ids, verifier_ids)


def list_folders(db: Session) -> list[CounterpartyFolderDto]:
    return [_folder_to_dto(item) for item in db.scalars(select(CounterpartyFolder).order_by(CounterpartyFolder.sort_order, CounterpartyFolder.id)).all()]


def create_folder(db: Session, payload: CounterpartyFolderCreatePayload) -> CounterpartyFolderDto:
    folder = CounterpartyFolder(parent_id=payload.parent_id, name=payload.name, sort_order=payload.sort_order, created_at=_now(), updated_at=_now())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return _folder_to_dto(folder)


def update_folder(db: Session, folder_id: int, payload: CounterpartyFolderUpdatePayload) -> CounterpartyFolderDto:
    folder = db.get(CounterpartyFolder, folder_id)
    if folder is None:
        raise ValueError("folder_not_found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(folder, field, value)
    folder.updated_at = _now()
    db.commit()
    db.refresh(folder)
    return _folder_to_dto(folder)


def list_counterparties(db: Session, include_archived: bool) -> list[CounterpartyDto]:
    query = select(Counterparty)
    if not include_archived:
        query = query.where(Counterparty.is_archived.is_(False))
    return [_counterparty_to_dto(item) for item in db.scalars(query.order_by(Counterparty.sort_order, Counterparty.id)).all()]


def get_counterparty_dto(db: Session, counterparty_id: int) -> CounterpartyDto:
    item = db.get(Counterparty, counterparty_id)
    if item is None:
        raise ValueError("counterparty_not_found")
    return _counterparty_to_dto(item)


def create_counterparty(db: Session, payload: CounterpartyUpsertPayload) -> CounterpartyDto:
    item = Counterparty(**payload.model_dump(), created_at=_now(), updated_at=_now())
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
    db.commit()
    db.refresh(item)
    return _counterparty_to_dto(item)


def archive_counterparty(db: Session, counterparty_id: int, archived: bool) -> CounterpartyDto:
    item = db.get(Counterparty, counterparty_id)
    if item is None:
        raise ValueError("counterparty_not_found")
    item.is_archived = archived
    item.updated_at = _now()
    db.commit()
    db.refresh(item)
    return _counterparty_to_dto(item)


def get_task_creator_settings(db: Session) -> CounterpartyTaskCreatorSettingsDto:
    settings = _get_settings(db)
    db.commit()
    return CounterpartyTaskCreatorSettingsDto(task_creator_user_id=settings.task_creator_user_id)


def update_task_creator_settings(db: Session, payload: CounterpartyTaskCreatorSettingsPayload) -> CounterpartyTaskCreatorSettingsDto:
    settings = _get_settings(db)
    settings.task_creator_user_id = payload.task_creator_user_id
    settings.updated_at = _now()
    db.commit()
    return CounterpartyTaskCreatorSettingsDto(task_creator_user_id=settings.task_creator_user_id)


def list_auto_task_rules(db: Session, counterparty_id: int) -> list[CounterpartyAutoTaskRuleDto]:
    counterparty = db.get(Counterparty, counterparty_id)
    if counterparty is None:
        raise ValueError("counterparty_not_found")
    rules = db.scalars(
        select(CounterpartyAutoTaskRule)
        .where(CounterpartyAutoTaskRule.counterparty_id == counterparty_id, CounterpartyAutoTaskRule.state != "deleted")
        .order_by(CounterpartyAutoTaskRule.id.desc())
    ).all()
    for rule in rules:
        ensure_horizon(db, rule)
    db.commit()
    effective_state = "paused" if counterparty.is_archived else None
    return [_rule_to_dto(db, rule, effective_state=effective_state if rule.state == "active" and counterparty.is_archived else None) for rule in rules]


def create_auto_task_rule(db: Session, counterparty_id: int, payload: CounterpartyAutoTaskRuleCreatePayload) -> CounterpartyAutoTaskRuleDto:
    counterparty = db.get(Counterparty, counterparty_id)
    if counterparty is None:
        raise ValueError("counterparty_not_found")
    settings = _get_settings(db)
    if settings.task_creator_user_id is None:
        raise ValueError("task_creator_user_id_not_configured")
    now = _now()
    rule = CounterpartyAutoTaskRule(
        counterparty_id=counterparty_id,
        task_kind=payload.task_kind,
        title_template=payload.title_template,
        description_template=payload.description_template,
        is_enabled=payload.is_enabled,
        schedule_weekday=payload.schedule_weekday,
        schedule_due_time=payload.schedule_due_time,
        horizon_days=payload.horizon_days,
        linked_task_master_id=None,
        state="active",
        created_at=now,
        updated_at=now,
    )
    db.add(rule)
    db.flush()
    for user_id in sorted({uid for uid in payload.assignee_user_ids if uid > 0}):
        db.add(CounterpartyAutoTaskRuleAssignee(rule_id=rule.id, user_id=user_id))
    for user_id in sorted({uid for uid in (payload.verifier_user_ids or []) if uid > 0}):
        db.add(CounterpartyAutoTaskRuleVerifier(rule_id=rule.id, user_id=user_id))

    master = _create_master_task(db, counterparty, rule, settings.task_creator_user_id)
    rule.linked_task_master_id = master.id
    _replace_task_links(db, master.id, payload.assignee_user_ids, payload.verifier_user_ids or [])
    ensure_horizon(db, rule)
    db.commit()
    db.refresh(rule)
    return _rule_to_dto(db, rule)


def update_auto_task_rule(db: Session, counterparty_id: int, rule_id: int, payload: CounterpartyAutoTaskRulePatchPayload, action: str | None) -> CounterpartyAutoTaskRuleDto:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id:
        raise ValueError("rule_not_found")
    counterparty = db.get(Counterparty, counterparty_id)
    if counterparty is None:
        raise ValueError("counterparty_not_found")

    updates = payload.model_dump(exclude_unset=True)
    schedule_changed = ("schedule_weekday" in updates and updates["schedule_weekday"] != rule.schedule_weekday) or (
        "schedule_due_time" in updates and updates["schedule_due_time"] != rule.schedule_due_time
    )
    if schedule_changed and action not in {"keep", "replace"}:
        raise ValueError("action_required")

    if schedule_changed and action == "keep":
        create_payload = CounterpartyAutoTaskRuleCreatePayload(
            task_kind=updates.get("task_kind", rule.task_kind),
            title_template=updates.get("title_template", rule.title_template),
            description_template=updates.get("description_template", rule.description_template),
            assignee_user_ids=updates.get("assignee_user_ids") or [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleAssignee.user_id).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id)).all()],
            verifier_user_ids=updates.get("verifier_user_ids") or [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleVerifier.user_id).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id)).all()],
            is_enabled=updates.get("is_enabled", rule.is_enabled),
            schedule_weekday=updates.get("schedule_weekday", rule.schedule_weekday),
            schedule_due_time=updates.get("schedule_due_time", rule.schedule_due_time),
            horizon_days=updates.get("horizon_days", rule.horizon_days),
        )
        db.commit()
        return create_auto_task_rule(db, counterparty_id, create_payload)

    if schedule_changed and action == "replace" and rule.linked_task_master_id:
        today = _now().date()
        db.execute(
            delete(Task).where(
                Task.recurrence_master_task_id == rule.linked_task_master_id,
                Task.status != "done",
                Task.due_date >= today,
            )
        )
        master = db.get(Task, rule.linked_task_master_id)
        if master:
            master.recurrence_state = "stopped"
        rule.state = "stopped"
        rule.updated_at = _now()
        db.flush()
        create_payload = CounterpartyAutoTaskRuleCreatePayload(
            task_kind=updates.get("task_kind", rule.task_kind),
            title_template=updates.get("title_template", rule.title_template),
            description_template=updates.get("description_template", rule.description_template),
            assignee_user_ids=updates.get("assignee_user_ids") or [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleAssignee.user_id).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id)).all()],
            verifier_user_ids=updates.get("verifier_user_ids") or [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleVerifier.user_id).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id)).all()],
            is_enabled=updates.get("is_enabled", rule.is_enabled),
            schedule_weekday=updates.get("schedule_weekday", rule.schedule_weekday),
            schedule_due_time=updates.get("schedule_due_time", rule.schedule_due_time),
            horizon_days=updates.get("horizon_days", rule.horizon_days),
        )
        db.commit()
        return create_auto_task_rule(db, counterparty_id, create_payload)

    for field in ["task_kind", "title_template", "description_template", "is_enabled", "schedule_weekday", "schedule_due_time", "horizon_days"]:
        if field in updates:
            setattr(rule, field, updates[field])
    if payload.assignee_user_ids is not None:
        db.execute(delete(CounterpartyAutoTaskRuleAssignee).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id))
        for user_id in sorted({uid for uid in payload.assignee_user_ids if uid > 0}):
            db.add(CounterpartyAutoTaskRuleAssignee(rule_id=rule.id, user_id=user_id))
    if payload.verifier_user_ids is not None:
        db.execute(delete(CounterpartyAutoTaskRuleVerifier).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id))
        for user_id in sorted({uid for uid in payload.verifier_user_ids if uid > 0}):
            db.add(CounterpartyAutoTaskRuleVerifier(rule_id=rule.id, user_id=user_id))

    master = db.get(Task, rule.linked_task_master_id) if rule.linked_task_master_id else None
    if master:
        master.title = _render_template(rule.title_template, counterparty) or ""
        master.description = _render_template(rule.description_template, counterparty)
        master.due_time = rule.schedule_due_time
        assignee_ids = payload.assignee_user_ids if payload.assignee_user_ids is not None else [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleAssignee.user_id).where(CounterpartyAutoTaskRuleAssignee.rule_id == rule.id)).all()]
        verifier_ids = payload.verifier_user_ids if payload.verifier_user_ids is not None else [row[0] for row in db.execute(select(CounterpartyAutoTaskRuleVerifier.user_id).where(CounterpartyAutoTaskRuleVerifier.rule_id == rule.id)).all()]
        _replace_task_links(db, master.id, assignee_ids, verifier_ids)

    rule.updated_at = _now()
    ensure_horizon(db, rule)
    db.commit()
    db.refresh(rule)
    return _rule_to_dto(db, rule)


def pause_auto_task_rule(db: Session, counterparty_id: int, rule_id: int) -> CounterpartyAutoTaskRuleDto:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id or rule.state == "deleted":
        raise ValueError("rule_not_found")
    rule.state = "paused"
    rule.updated_at = _now()
    db.commit()
    return _rule_to_dto(db, rule)


def resume_auto_task_rule(db: Session, counterparty_id: int, rule_id: int) -> CounterpartyAutoTaskRuleDto:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id or rule.state == "deleted":
        raise ValueError("rule_not_found")
    rule.state = "active"
    rule.updated_at = _now()
    ensure_horizon(db, rule)
    db.commit()
    return _rule_to_dto(db, rule)


def stop_auto_task_rule(db: Session, counterparty_id: int, rule_id: int) -> CounterpartyAutoTaskRuleDto:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id or rule.state == "deleted":
        raise ValueError("rule_not_found")
    rule.state = "stopped"
    rule.updated_at = _now()
    master = db.get(Task, rule.linked_task_master_id) if rule.linked_task_master_id else None
    if master:
        master.recurrence_state = "stopped"
    db.commit()
    return _rule_to_dto(db, rule)


def delete_auto_task_rule(db: Session, counterparty_id: int, rule_id: int) -> None:
    rule = db.get(CounterpartyAutoTaskRule, rule_id)
    if rule is None or rule.counterparty_id != counterparty_id or rule.state == "deleted":
        raise ValueError("rule_not_found")
    rule.state = "deleted"
    rule.is_enabled = False
    rule.updated_at = _now()

    master = db.get(Task, rule.linked_task_master_id) if rule.linked_task_master_id else None
    if master:
        master.recurrence_state = "stopped"
        db.execute(
            delete(Task).where(
                Task.recurrence_master_task_id == master.id,
                Task.status != "done",
                Task.due_date >= _now().date(),
            )
        )
    db.commit()
