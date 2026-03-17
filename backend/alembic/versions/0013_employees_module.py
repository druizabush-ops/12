"""Добавляет модуль Сотрудники, оргструктуру и роли.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0013_employees_module"
down_revision = "0012_counterparty_autotasks_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("login", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_login", "users", ["login"], unique=True)

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

    op.create_table(
        "user_organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("head_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "parent_group_id", "name", name="uq_group_parent_name"),
    )
    op.create_index("ix_groups_org_parent", "groups", ["organization_id", "parent_group_id"], unique=False)

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
        sa.UniqueConstraint("group_id", "name", name="uq_position_group_name"),
    )
    op.create_index("ix_positions_org_group", "positions", ["organization_id", "group_id"], unique=False)

    op.create_table(
        "user_positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
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

    bind = op.get_bind()
    bind.execute(
        text(
            """
            INSERT INTO platform_modules (id, name, title, path, "order", is_primary)
            VALUES ('employees', 'employees', 'Сотрудники', 'employees', 4, false)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )
    bind.execute(
        text(
            """
            INSERT INTO auth_role_modules (role_id, module_id)
            SELECT 1, 'employees'
            WHERE NOT EXISTS (
                SELECT 1 FROM auth_role_modules WHERE role_id = 1 AND module_id = 'employees'
            )
            """
        )
    )

    perms = [
        ("users", "view", "users.view", "Просмотр пользователей"),
        ("users", "create", "users.create", "Создание пользователей"),
        ("users", "edit", "users.edit", "Редактирование пользователей"),
        ("users", "archive", "users.archive", "Архивирование пользователей"),
        ("users", "set_password", "users.set_password", "Сброс пароля пользователей"),
        ("orgstructure", "view", "orgstructure.view", "Просмотр оргструктуры"),
        ("orgstructure", "edit", "orgstructure.edit", "Редактирование оргструктуры"),
        ("roles", "view", "roles.view", "Просмотр ролей"),
        ("roles", "create", "roles.create", "Создание ролей"),
        ("roles", "edit", "roles.edit", "Редактирование ролей"),
        ("roles", "archive", "roles.archive", "Архивирование ролей"),
        ("roles", "delete", "roles.delete", "Удаление ролей"),
        ("organizations", "switch", "organizations.switch", "Переключение организации"),
        ("organizations", "manage", "organizations.manage", "Управление организациями"),
        ("admin", "view", "admin.view", "Просмотр админ-раздела"),
        ("employees", "view", "employees.view", "Просмотр модуля сотрудники"),
    ]
    for module, action, code, name in perms:
        bind.execute(
            text(
                """
                INSERT INTO permissions (module, action, code, name)
                VALUES (:module, :action, :code, :name)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            {"module": module, "action": action, "code": code, "name": name},
        )
        bind.execute(
            text(
                """
                INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
                VALUES (1, 'employees', :permission, true)
                ON CONFLICT (role_id, module_id, permission) DO NOTHING
                """
            ),
            {"permission": code},
        )

    bind.execute(
        text(
            """
            INSERT INTO roles (name, code, description, is_system, is_active, is_archived)
            VALUES ('SUPER_ADMIN', 'SUPER_ADMIN', 'Системная роль с полным доступом', true, true, false)
            ON CONFLICT (code) DO NOTHING
            """
        )
    )
    bind.execute(
        text(
            """
            INSERT INTO users (id, full_name, login, password_hash, phone, is_active, is_archived)
            VALUES (1, 'Системный администратор', 'admin', :password_hash, NULL, true, false)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"password_hash": "$2b$12$6L/KwVRtpAkuGiST07XHqOPvuTDn7qrA6gfkhhjVwX.KjdHc9aOSq"},
    )


def downgrade() -> None:
    op.execute("DELETE FROM auth_role_module_permissions WHERE module_id = 'employees'")
    op.execute("DELETE FROM auth_role_modules WHERE module_id = 'employees'")
    op.execute("DELETE FROM platform_modules WHERE id = 'employees'")
    op.execute("DELETE FROM users WHERE id = 1 AND login = 'admin'")
    op.execute("DELETE FROM roles WHERE code = 'SUPER_ADMIN'")
    op.drop_table("position_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("user_positions")
    op.drop_index("ix_positions_org_group", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_groups_org_parent", table_name="groups")
    op.drop_table("groups")
    op.drop_table("user_organizations")
    op.drop_table("organizations")
    op.drop_index("ix_users_login", table_name="users")
    op.drop_table("users")
