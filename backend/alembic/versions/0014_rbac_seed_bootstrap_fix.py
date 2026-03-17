"""Идемпотентный bootstrap RBAC для SUPER_ADMIN и модулей admin/employees."""

from alembic import op
import sqlalchemy as sa


revision = "0014_rbac_seed_bootstrap_fix"
down_revision = "0013_employees_module"
branch_labels = None
depends_on = None


PERMISSION_CODES = [
    "users.view",
    "users.create",
    "users.edit",
    "users.archive",
    "users.set_password",
    "orgstructure.view",
    "orgstructure.edit",
    "roles.view",
    "roles.create",
    "roles.edit",
    "roles.archive",
    "roles.delete",
    "organizations.switch",
    "organizations.manage",
    "admin.view",
    "employees.view",
]


def _sync_sequence(bind: sa.engine.Connection, table_name: str, column_name: str = "id") -> None:
    """Выравнивает sequence с максимальным id в PostgreSQL перед seed-вставками."""

    if bind.dialect.name != "postgresql":
        return

    bind.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence(:table_name, :column_name),
                COALESCE((SELECT MAX(id) FROM auth_roles), 1),
                true
            )
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )


def upgrade() -> None:
    bind = op.get_bind()

    _sync_sequence(bind, "auth_roles", "id")

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_roles (name, can_manage_access)
            SELECT 'SUPER_ADMIN', true
            WHERE NOT EXISTS (
                SELECT 1 FROM auth_roles WHERE name = 'SUPER_ADMIN'
            )
            """
        )
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_role_modules (role_id, module_id)
            SELECT r.id, m.id
            FROM auth_roles r
            JOIN platform_modules m ON true
            WHERE r.name = 'SUPER_ADMIN'
              AND NOT EXISTS (
                  SELECT 1
                  FROM auth_role_modules rm
                  WHERE rm.role_id = r.id
                    AND rm.module_id = m.id
              )
            """
        )
    )

    for code in PERMISSION_CODES:
        module_id = "admin" if code.startswith("admin.") else "employees"
        bind.execute(
            sa.text(
                """
                INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
                SELECT r.id, :module_id, :permission, true
                FROM auth_roles r
                WHERE r.name = 'SUPER_ADMIN'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM auth_role_module_permissions p
                      WHERE p.role_id = r.id
                        AND p.module_id = :module_id
                        AND p.permission = :permission
                  )
                """
            ),
            {"module_id": module_id, "permission": code},
        )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM auth_users u
            JOIN auth_roles r ON r.name = 'SUPER_ADMIN'
            WHERE u.username = 'admin'
              AND NOT EXISTS (
                  SELECT 1
                  FROM auth_user_roles ur
                  WHERE ur.user_id = u.id
                    AND ur.role_id = r.id
              )
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_module_permissions
            WHERE role_id IN (
                SELECT id FROM auth_roles WHERE name = 'SUPER_ADMIN'
            )
              AND permission IN (
                'users.view',
                'users.create',
                'users.edit',
                'users.archive',
                'users.set_password',
                'orgstructure.view',
                'orgstructure.edit',
                'roles.view',
                'roles.create',
                'roles.edit',
                'roles.archive',
                'roles.delete',
                'organizations.switch',
                'organizations.manage',
                'admin.view',
                'employees.view'
              )
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_modules
            WHERE role_id IN (
                SELECT id FROM auth_roles WHERE name = 'SUPER_ADMIN'
            )
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_user_roles
            WHERE role_id IN (
                SELECT id FROM auth_roles WHERE name = 'SUPER_ADMIN'
            )
            """
        )
    )

    bind.execute(sa.text("DELETE FROM auth_roles WHERE name = 'SUPER_ADMIN'"))
