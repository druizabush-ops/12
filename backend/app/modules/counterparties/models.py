from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

CounterpartyStatus = Literal["active", "inactive"]
CounterpartyAutoTaskKind = Literal["order_request", "custom"]


class CounterpartyFolder(Base):
    __tablename__ = "counterparty_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("counterparty_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Counterparty(Base):
    __tablename__ = "counterparties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty_folders.id", ondelete="RESTRICT"), nullable=False)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[CounterpartyStatus] = mapped_column(String(16), nullable=False, default="active")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messenger: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_deadline_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    delivery_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defect_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    inn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    kpp: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    legal_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_bik: Mapped[str | None] = mapped_column(String(32), nullable=True)
    account: Mapped[str | None] = mapped_column(String(64), nullable=True)
    corr_account: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CounterpartyAutoTaskRule(Base):
    __tablename__ = "counterparty_auto_task_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparties.id", ondelete="CASCADE"), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[CounterpartyAutoTaskKind] = mapped_column(String(32), nullable=False, default="order_request")

    recurrence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    recurrence_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    recurrence_days_of_week: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recurrence_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    primary_assignee_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False)
    primary_text: Mapped[str] = mapped_column(Text, nullable=False)
    primary_due_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    review_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_assignee_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_due_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CounterpartyAutoTaskBinding(Base):
    __tablename__ = "counterparty_auto_task_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty_auto_task_rules.id", ondelete="CASCADE"), nullable=False, unique=True)
    primary_master_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    review_master_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
