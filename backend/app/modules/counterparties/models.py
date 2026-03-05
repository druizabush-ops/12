from __future__ import annotations

from datetime import datetime, time
from typing import Literal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

CounterpartyStatus = Literal["active", "inactive"]
CounterpartyAutoTaskKind = Literal["MAKE_ORDER", "SEND_ORDER"]
CounterpartyAutoTaskState = Literal["active", "paused", "stopped", "deleted"]


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
    task_kind: Mapped[CounterpartyAutoTaskKind] = mapped_column(String(32), nullable=False)
    title_template: Mapped[str] = mapped_column(String(255), nullable=False)
    description_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    schedule_weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    schedule_due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    linked_task_master_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    state: Mapped[CounterpartyAutoTaskState] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CounterpartyAutoTaskRuleAssignee(Base):
    __tablename__ = "counterparty_auto_task_rule_assignees"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty_auto_task_rules.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True)


class CounterpartyAutoTaskRuleVerifier(Base):
    __tablename__ = "counterparty_auto_task_rule_verifiers"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty_auto_task_rules.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True)


class CounterpartyModuleSettings(Base):
    __tablename__ = "counterparty_module_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_creator_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
