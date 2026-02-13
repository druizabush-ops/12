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


Index("ix_tasks_due_date", Task.due_date)
Index("ix_tasks_due_at", Task.due_at)
Index("ix_tasks_status", Task.status)


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
