"""Добавляет модуль сотрудников, оргструктуру и роли."""

from alembic import op
import sqlalchemy as sa

revision = "0013_employees_module"
down_revision = "0012_counterparty_autotasks_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("auth_users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("auth_users", sa.Column("phone", sa.String(length=64), nullable=True))
    op.add_column("auth_users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("auth_users", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("auth_users", sa.Column("last_organization_id", sa.Integer(), nullable=True))
    op.add_column("auth_users", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("auth_users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.execute(sa.text("UPDATE auth_users SET full_name = username WHERE full_name IS NULL"))
    op.alter_column("auth_users", "full_name", nullable=False)

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_code", "organizations", ["code"], unique=True)

    op.create_table(
        "user_organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("head_user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "parent_group_id", "name", name="uq_group_name_in_parent"),
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("manager_position_id", sa.Integer(), sa.ForeignKey("positions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("group_id", "name", name="uq_position_name_in_group"),
    )

    op.create_table(
        "user_positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "position_id", name="uq_user_position"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "position_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("position_id", "role_id", name="uq_position_role"),
    )

    op.execute(sa.text("""
        INSERT INTO platform_modules (id, name, title, path, \"order\", is_primary)
        VALUES ('employees', 'employees', 'Сотрудники', 'employees', 4, false)
        ON CONFLICT (id) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO organizations (name, code, is_active, is_archived)
        VALUES ('Организация по умолчанию', 'DEFAULT', true, false)
        ON CONFLICT (code) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO auth_role_modules (role_id, module_id)
        SELECT id, 'employees' FROM auth_roles WHERE name='admin'
        ON CONFLICT DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO roles (name, code, description, is_system, is_active, is_archived)
        VALUES ('Супер администратор', 'SUPER_ADMIN', 'Системная роль полного доступа', true, true, false)
        ON CONFLICT (code) DO NOTHING
    """))

    permissions = [
        ('users', 'view', 'users.view', 'Просмотр пользователей'),
        ('users', 'create', 'users.create', 'Создание пользователей'),
        ('users', 'edit', 'users.edit', 'Редактирование пользователей'),
        ('users', 'archive', 'users.archive', 'Архивирование пользователей'),
        ('users', 'set_password', 'users.set_password', 'Смена пароля пользователей'),
        ('orgstructure', 'view', 'orgstructure.view', 'Просмотр оргструктуры'),
        ('orgstructure', 'edit', 'orgstructure.edit', 'Изменение оргструктуры'),
        ('roles', 'view', 'roles.view', 'Просмотр ролей'),
        ('roles', 'create', 'roles.create', 'Создание ролей'),
        ('roles', 'edit', 'roles.edit', 'Редактирование ролей'),
        ('roles', 'archive', 'roles.archive', 'Архивирование ролей'),
        ('roles', 'delete', 'roles.delete', 'Удаление ролей'),
        ('organizations', 'switch', 'organizations.switch', 'Переключение организаций'),
        ('organizations', 'manage', 'organizations.manage', 'Управление организациями'),
    ]
    for module, action, code, name in permissions:
        op.execute(
            sa.text(
                "INSERT INTO permissions (module, action, code, name) VALUES (:module, :action, :code, :name) ON CONFLICT (code) DO NOTHING"
            ),
            {"module": module, "action": action, "code": code, "name": name},
        )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM platform_modules WHERE id='employees'"))
    op.drop_table("position_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("user_positions")
    op.drop_table("positions")
    op.drop_table("groups")
    op.drop_table("user_organizations")
    op.drop_index("ix_organizations_code", table_name="organizations")
    op.drop_table("organizations")
    op.drop_column("auth_users", "updated_at")
    op.drop_column("auth_users", "created_at")
    op.drop_column("auth_users", "last_organization_id")
    op.drop_column("auth_users", "is_archived")
    op.drop_column("auth_users", "is_active")
    op.drop_column("auth_users", "phone")
    op.drop_column("auth_users", "full_name")
