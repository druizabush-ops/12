from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from io import BytesIO
from typing import Any
from uuid import uuid4

from fastapi import Header, HTTPException, UploadFile
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.tasks.models import Task, TaskAssignee, TaskVerifier

BATCH_SIZE = 500

EXCEL_HEADERS = [
    "id",
    "title",
    "description",
    "due_date",
    "due_time",
    "priority",
    "status",
    "created_by_user_id",
    "assignee_user_ids",
    "verifier_user_ids",
    "completed_at",
    "is_recurring",
    "recurrence_type",
    "recurrence_interval",
    "recurrence_days_of_week",
    "recurrence_end_date",
]

PRIORITY_RU_TO_EN = {
    "обычная": "normal",
    "срочно": "urgent",
    "очень срочно": "very_urgent",
}

WEEKDAY_RU_TO_NUM = {
    "пн": "1",
    "вт": "2",
    "ср": "3",
    "чт": "4",
    "пт": "5",
    "сб": "6",
    "вс": "7",
}


@dataclass
class ImportErrorItem:
    row: int
    message: str


@dataclass
class ParsedTaskRow:
    row_number: int
    task_id: str
    is_update: bool
    task_mapping: dict[str, Any]
    assignee_ids: list[int]
    verifier_ids: list[int]


@dataclass
class ParsedWorkbook:
    rows: list[ParsedTaskRow]
    would_create: int
    would_update: int
    skipped: int
    errors: list[ImportErrorItem]
    warnings: list[ImportErrorItem]


def validate_admin_pin(x_tasks_admin_pin: str | None = Header(default=None)) -> None:
    expected = os.getenv("TASKS_ADMIN_PIN", "0000")
    if (x_tasks_admin_pin or "") != expected:
        raise HTTPException(status_code=403, detail="Invalid admin PIN")


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_date_value(value: Any, field: str) -> date | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field}: ожидается формат YYYY-MM-DD") from exc


def _parse_time_value(value: Any, field: str) -> time | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        return time.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field}: ожидается формат HH:MM") from exc


def _parse_datetime_value(value: Any, field: str) -> datetime | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M")
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{field}: ожидается формат YYYY-MM-DD HH:MM") from exc


def _parse_priority(value: Any) -> str:
    text = _as_text(value)
    if not text:
        return "normal"
    normalized = text.lower()
    mapped = PRIORITY_RU_TO_EN.get(normalized, normalized)
    if mapped not in {"normal", "urgent", "very_urgent"}:
        raise ValueError("priority: допустимы normal/urgent/very_urgent")
    return mapped


def _parse_status(value: Any) -> str:
    text = _as_text(value)
    if not text:
        return "active"
    normalized = text.lower()
    if normalized == "done_pending_verify":
        raise ValueError("status: done_pending_verify импортировать нельзя")
    if normalized not in {"active", "done"}:
        raise ValueError("status: допустимы active/done")
    return normalized


def _parse_bool(value: Any, default: bool = False) -> bool:
    text = _as_text(value)
    if not text:
        return default
    if text.lower() in {"true", "1", "yes", "да"}:
        return True
    if text.lower() in {"false", "0", "no", "нет"}:
        return False
    raise ValueError("is_recurring: допустимы TRUE/FALSE")


def _parse_int(value: Any, field: str, default: int | None = None) -> int | None:
    text = _as_text(value)
    if not text:
        return default
    try:
        number = int(text)
    except ValueError as exc:
        raise ValueError(f"{field}: ожидается число") from exc
    return number


def _parse_user_ids(value: Any, field: str) -> list[int]:
    text = _as_text(value)
    if not text:
        return []
    result: list[int] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        try:
            result.append(int(item))
        except ValueError as exc:
            raise ValueError(f"{field}: неверный ID '{item}'") from exc
    return sorted(set(result))


def _parse_weekdays(value: Any) -> str | None:
    text = _as_text(value)
    if not text:
        return None
    values = [item.strip().lower() for item in text.split(",") if item.strip()]
    normalized: list[str] = []
    for item in values:
        if item in WEEKDAY_RU_TO_NUM:
            normalized.append(WEEKDAY_RU_TO_NUM[item])
            continue
        if item in {"1", "2", "3", "4", "5", "6", "7"}:
            normalized.append(item)
            continue
        raise ValueError("recurrence_days_of_week: допустимы 1..7 или Пн..Вс")
    return ",".join(sorted(set(normalized), key=int))


def _validate_users_exist(db: Session, user_ids: list[int], field: str, cache: dict[int, bool]) -> None:
    for user_id in user_ids:
        exists = cache.get(user_id)
        if exists is None:
            exists = db.scalar(select(User.id).where(User.id == user_id).limit(1)) is not None
            cache[user_id] = exists
        if not exists:
            raise ValueError(f"{field}: пользователь {user_id} не найден")


def build_template_workbook() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "tasks_template"

    for col, header in enumerate(EXCEL_HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        if header in {"title", "created_by_user_id"}:
            cell.font = Font(bold=True)

    example = [
        "",
        "Проверить документы",
        "Пример задачи из шаблона",
        "2026-03-10",
        "10:30",
        "normal",
        "active",
        "1",
        "1,2",
        "",
        "",
        "FALSE",
        "weekly",
        "1",
        "1,3,5",
        "2026-12-31",
    ]
    for col, value in enumerate(example, start=1):
        ws.cell(row=2, column=col, value=value)

    stream = BytesIO()
    wb.save(stream)
    return stream.getvalue()


def export_tasks_workbook(db: Session) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "tasks_export"
    ws.append(EXCEL_HEADERS)

    tasks = db.scalars(select(Task).order_by(Task.created_at.asc(), Task.id.asc())).all()
    task_ids = [task.id for task in tasks]
    assignee_rows = db.execute(select(TaskAssignee.task_id, TaskAssignee.user_id).where(TaskAssignee.task_id.in_(task_ids))).all() if task_ids else []
    verifier_rows = db.execute(select(TaskVerifier.task_id, TaskVerifier.user_id).where(TaskVerifier.task_id.in_(task_ids))).all() if task_ids else []

    assignee_map: dict[str, list[int]] = {}
    for task_id, user_id in assignee_rows:
        assignee_map.setdefault(task_id, []).append(user_id)

    verifier_map: dict[str, list[int]] = {}
    for task_id, user_id in verifier_rows:
        verifier_map.setdefault(task_id, []).append(user_id)

    for task in tasks:
        ws.append(
            [
                task.id,
                task.title,
                task.description,
                task.due_date.isoformat() if task.due_date else "",
                task.due_time.strftime("%H:%M") if task.due_time else "",
                task.priority or "",
                task.status,
                task.created_by_user_id,
                ",".join(str(item) for item in sorted(set(assignee_map.get(task.id, [])))),
                ",".join(str(item) for item in sorted(set(verifier_map.get(task.id, [])))),
                task.completed_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if task.completed_at else "",
                "TRUE" if task.is_recurring else "FALSE",
                task.recurrence_type or "",
                task.recurrence_interval or "",
                task.recurrence_days_of_week or "",
                task.recurrence_end_date.isoformat() if task.recurrence_end_date else "",
            ]
        )

    stream = BytesIO()
    wb.save(stream)
    return stream.getvalue()


def _validate_headers(sheet: Any) -> None:
    header_values = [_as_text(sheet.cell(row=1, column=index + 1).value) for index in range(len(EXCEL_HEADERS))]
    if header_values != EXCEL_HEADERS:
        raise HTTPException(status_code=400, detail="Invalid template headers")


def _parse_workbook(db: Session, upload: UploadFile) -> ParsedWorkbook:
    if not upload.filename or not upload.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    content = upload.file.read()
    workbook = load_workbook(filename=BytesIO(content), data_only=True)
    sheet = workbook.active
    _validate_headers(sheet)

    user_exists_cache: dict[int, bool] = {}
    existing_cache: dict[str, bool] = {}

    rows: list[ParsedTaskRow] = []
    errors: list[ImportErrorItem] = []
    warnings: list[ImportErrorItem] = []
    would_create = 0
    would_update = 0
    skipped = 0

    for row_number, row in enumerate(sheet.iter_rows(min_row=2, max_col=len(EXCEL_HEADERS), values_only=True), start=2):
        values = list(row) if row is not None else []
        if not values or all(_as_text(item) == "" for item in values):
            skipped += 1
            continue

        try:
            row_data = {EXCEL_HEADERS[index]: values[index] for index in range(len(EXCEL_HEADERS))}
            title = _as_text(row_data["title"])
            if not title:
                raise ValueError("title: обязательное поле")

            creator_id = _parse_int(row_data["created_by_user_id"], "created_by_user_id")
            if creator_id is None:
                raise ValueError("created_by_user_id: обязательное поле")
            _validate_users_exist(db, [creator_id], "created_by_user_id", user_exists_cache)

            due_date = _parse_date_value(row_data["due_date"], "due_date")
            due_time = _parse_time_value(row_data["due_time"], "due_time")
            priority = _parse_priority(row_data["priority"])
            status = _parse_status(row_data["status"])
            completed_at = _parse_datetime_value(row_data["completed_at"], "completed_at")
            if status == "done" and completed_at is None:
                raise ValueError("completed_at обязателен при status=done")
            if status != "done":
                completed_at = None

            is_recurring = _parse_bool(row_data["is_recurring"], default=False)
            recurrence_type = _as_text(row_data["recurrence_type"]) or None
            if recurrence_type and recurrence_type not in {"daily", "weekly", "monthly", "yearly"}:
                raise ValueError("recurrence_type: допустимы daily/weekly/monthly/yearly")

            recurrence_interval = _parse_int(row_data["recurrence_interval"], "recurrence_interval", default=1)
            if recurrence_interval is not None and recurrence_interval < 1:
                raise ValueError("recurrence_interval: значение должно быть >= 1")

            recurrence_days = _parse_weekdays(row_data["recurrence_days_of_week"])
            recurrence_end_date = _parse_date_value(row_data["recurrence_end_date"], "recurrence_end_date")

            assignee_ids = _parse_user_ids(row_data["assignee_user_ids"], "assignee_user_ids")
            verifier_ids = _parse_user_ids(row_data["verifier_user_ids"], "verifier_user_ids")
            if not assignee_ids:
                assignee_ids = [creator_id]

            _validate_users_exist(db, assignee_ids, "assignee_user_ids", user_exists_cache)
            _validate_users_exist(db, verifier_ids, "verifier_user_ids", user_exists_cache)

            task_id = _as_text(row_data["id"]) or str(uuid4())
            is_update = False
            if _as_text(row_data["id"]):
                cached = existing_cache.get(task_id)
                if cached is None:
                    cached = db.scalar(select(Task.id).where(Task.id == task_id).limit(1)) is not None
                    existing_cache[task_id] = cached
                is_update = cached
                if not is_update:
                    warnings.append(ImportErrorItem(row=row_number, message=f"id {task_id} не найден, будет создана новая задача"))

            rows.append(
                ParsedTaskRow(
                    row_number=row_number,
                    task_id=task_id,
                    is_update=is_update,
                    task_mapping={
                        "id": task_id,
                        "title": title,
                        "description": _as_text(row_data["description"]) or None,
                        "due_date": due_date,
                        "due_time": due_time,
                        "priority": priority,
                        "status": status,
                        "created_by_user_id": creator_id,
                        "completed_at": completed_at,
                        "verified_at": None,
                        "source_type": None,
                        "source_id": None,
                        "source_module": None,
                        "source_counterparty_id": None,
                        "source_trigger_id": None,
                        "is_recurring": is_recurring,
                        "recurrence_type": recurrence_type if is_recurring else None,
                        "recurrence_interval": recurrence_interval if is_recurring else None,
                        "recurrence_days_of_week": recurrence_days if is_recurring else None,
                        "recurrence_end_date": recurrence_end_date if is_recurring else None,
                        "recurrence_master_task_id": None,
                        "recurrence_state": "active",
                        "is_hidden": False,
                    },
                    assignee_ids=assignee_ids,
                    verifier_ids=verifier_ids,
                )
            )
            if is_update:
                would_update += 1
            else:
                would_create += 1

        except ValueError as exc:
            errors.append(ImportErrorItem(row=row_number, message=str(exc)))
            skipped += 1

    return ParsedWorkbook(
        rows=rows,
        would_create=would_create,
        would_update=would_update,
        skipped=skipped,
        errors=errors,
        warnings=warnings,
    )


def preview_import_tasks_workbook(db: Session, upload: UploadFile) -> dict[str, Any]:
    parsed = _parse_workbook(db, upload)
    return {
        "would_create": parsed.would_create,
        "would_update": parsed.would_update,
        "would_skip": parsed.skipped,
        "errors": [{"row": item.row, "message": item.message} for item in parsed.errors],
        "warnings": [{"row": item.row, "message": item.message} for item in parsed.warnings],
    }


def _chunks(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def import_tasks_workbook(db: Session, upload: UploadFile) -> dict[str, Any]:
    parsed = _parse_workbook(db, upload)

    create_rows = [item for item in parsed.rows if not item.is_update]
    update_rows = [item for item in parsed.rows if item.is_update]

    errors = list(parsed.errors)
    created = 0
    updated = 0
    skipped = parsed.skipped

    try:
        with db.begin():
            for batch in _chunks(create_rows, BATCH_SIZE):
                try:
                    with db.begin_nested():
                        now = datetime.now(timezone.utc)
                        mappings = [dict(item.task_mapping, created_at=now) for item in batch]
                        db.bulk_insert_mappings(Task, mappings)

                        assignee_rows = [
                            {"task_id": item.task_id, "user_id": user_id}
                            for item in batch
                            for user_id in item.assignee_ids
                        ]
                        verifier_rows = [
                            {"task_id": item.task_id, "user_id": user_id}
                            for item in batch
                            for user_id in item.verifier_ids
                        ]
                        if assignee_rows:
                            db.bulk_insert_mappings(TaskAssignee, assignee_rows)
                        if verifier_rows:
                            db.bulk_insert_mappings(TaskVerifier, verifier_rows)
                    created += len(batch)
                except SQLAlchemyError as exc:
                    skipped += len(batch)
                    errors.extend(ImportErrorItem(row=item.row_number, message=f"Ошибка batch insert: {exc.__class__.__name__}") for item in batch)

            for batch in _chunks(update_rows, BATCH_SIZE):
                try:
                    with db.begin_nested():
                        db.bulk_update_mappings(Task, [item.task_mapping for item in batch])
                        batch_ids = [item.task_id for item in batch]
                        db.query(TaskAssignee).filter(TaskAssignee.task_id.in_(batch_ids)).delete(synchronize_session=False)
                        db.query(TaskVerifier).filter(TaskVerifier.task_id.in_(batch_ids)).delete(synchronize_session=False)

                        assignee_rows = [
                            {"task_id": item.task_id, "user_id": user_id}
                            for item in batch
                            for user_id in item.assignee_ids
                        ]
                        verifier_rows = [
                            {"task_id": item.task_id, "user_id": user_id}
                            for item in batch
                            for user_id in item.verifier_ids
                        ]
                        if assignee_rows:
                            db.bulk_insert_mappings(TaskAssignee, assignee_rows)
                        if verifier_rows:
                            db.bulk_insert_mappings(TaskVerifier, verifier_rows)
                    updated += len(batch)
                except SQLAlchemyError as exc:
                    skipped += len(batch)
                    errors.extend(ImportErrorItem(row=item.row_number, message=f"Ошибка batch update: {exc.__class__.__name__}") for item in batch)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Import failed")

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": [{"row": item.row, "message": item.message} for item in errors],
    }
