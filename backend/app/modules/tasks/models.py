from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    urgency: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    requires_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verifier_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("auth_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    folder_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("task_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    recurrence_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recurrence_days_of_week: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recurrence_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurrence_master_task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    recurrence_state: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


Index("ix_tasks_due_date", Task.due_date)
Index("ix_tasks_due_at", Task.due_at)
Index("ix_tasks_status", Task.status)
Index("ix_tasks_folder_id", Task.folder_id)
Index("ix_tasks_recurrence_master_task_id", Task.recurrence_master_task_id)


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class TaskFolder(Base):
    __tablename__ = "task_folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    show_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_overdue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_task_folders_created_by_user_id", TaskFolder.created_by_user_id)
