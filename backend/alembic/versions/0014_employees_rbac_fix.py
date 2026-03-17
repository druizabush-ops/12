"""Доводит bootstrap RBAC для employees/admin до рабочего состояния."""

from alembic import op
import sqlalchemy as sa


revision = "0014_employees_rbac_fix"
down_revision = "0013_employees_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_roles (name, can_manage_access)
            VALUES ('SUPER_ADMIN', true)
            ON CONFLICT (name) DO NOTHING
            """
        )
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_role_modules (role_id, module_id)
            SELECT r.id, pm.id
            FROM auth_roles r
            CROSS JOIN platform_modules pm
            WHERE r.name = 'SUPER_ADMIN'
            ON CONFLICT (role_id, module_id) DO NOTHING
            """
        )
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM auth_users u
            JOIN auth_roles r ON r.name = 'SUPER_ADMIN'
            WHERE u.username = 'admin'
            ON CONFLICT (user_id, role_id) DO NOTHING
            """
        )
    )

    permissions = [
        ("admin", "view"),
        ("admin", "create"),
        ("admin", "edit"),
        ("admin", "delete"),
        ("employees", "users.view"),
        ("employees", "users.create"),
        ("employees", "users.edit"),
        ("employees", "users.archive"),
        ("employees", "users.set_password"),
        ("employees", "orgstructure.view"),
        ("employees", "orgstructure.edit"),
        ("employees", "roles.view"),
        ("employees", "roles.create"),
        ("employees", "roles.edit"),
        ("employees", "roles.archive"),
        ("employees", "roles.delete"),
        ("employees", "organizations.switch"),
        ("employees", "organizations.manage"),
        ("employees", "admin.view"),
        ("employees", "employees.view"),
    ]

    for module_id, permission in permissions:
        bind.execute(
            sa.text(
                """
                INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
                SELECT r.id, :module_id, :permission, true
                FROM auth_roles r
                WHERE r.name = 'SUPER_ADMIN'
                ON CONFLICT (role_id, module_id, permission) DO NOTHING
                """
            ),
            {"module_id": module_id, "permission": permission},
        )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_user_roles aur
            USING auth_users u, auth_roles r
            WHERE aur.user_id = u.id
              AND aur.role_id = r.id
              AND u.username = 'admin'
              AND r.name = 'SUPER_ADMIN'
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_module_permissions armp
            USING auth_roles r
            WHERE armp.role_id = r.id
              AND r.name = 'SUPER_ADMIN'
              AND (
                (armp.module_id = 'admin' AND armp.permission IN ('view', 'create', 'edit', 'delete'))
                OR
                (armp.module_id = 'employees' AND armp.permission IN (
                    'users.view', 'users.create', 'users.edit', 'users.archive', 'users.set_password',
                    'orgstructure.view', 'orgstructure.edit', 'roles.view', 'roles.create', 'roles.edit',
                    'roles.archive', 'roles.delete', 'organizations.switch', 'organizations.manage',
                    'admin.view', 'employees.view'
                ))
              )
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_modules arm
            USING auth_roles r
            WHERE arm.role_id = r.id
              AND r.name = 'SUPER_ADMIN'
            """
        )
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_roles r
            WHERE r.name = 'SUPER_ADMIN'
              AND NOT EXISTS (
                  SELECT 1 FROM auth_user_roles aur WHERE aur.role_id = r.id
              )
            """
        )
    )
