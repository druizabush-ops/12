"""Идемпотентный bootstrap RBAC для модулей admin и employees."""

from alembic import op
import sqlalchemy as sa

revision = "0014_employees_rbac_bootstrap_fix"
down_revision = "0013_employees_module"
branch_labels = None
depends_on = None


SUPER_ADMIN_ROLE = "SUPER_ADMIN"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD_HASH = "$2b$12$6L/KwVRtpAkuGiST07XHqOPvuTDn7qrA6gfkhhjVwX.KjdHc9aOSq"

PERMISSIONS = [
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
    ("admin", "admin.view"),
    ("employees", "employees.view"),
]


MODULES = ["admin", "employees"]


def _sync_sequences(bind: sa.engine.Connection) -> None:
    if bind.dialect.name != "postgresql":
        return

    bind.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('auth_roles', 'id'),
                COALESCE((SELECT MAX(id) FROM auth_roles), 1),
                true
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('auth_users', 'id'),
                COALESCE((SELECT MAX(id) FROM auth_users), 1),
                true
            )
            """
        )
    )


def upgrade() -> None:
    bind = op.get_bind()

    _sync_sequences(bind)

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_roles (name, can_manage_access)
            SELECT CAST(:role_name AS VARCHAR), true
            WHERE NOT EXISTS (
                SELECT 1
                FROM auth_roles
                WHERE name = CAST(:role_name AS VARCHAR)
            )
            """
        ).bindparams(sa.bindparam("role_name", type_=sa.String(length=255))),
        {"role_name": SUPER_ADMIN_ROLE},
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_users (username, hashed_password)
            SELECT CAST(:username AS VARCHAR), CAST(:password_hash AS VARCHAR)
            WHERE NOT EXISTS (
                SELECT 1
                FROM auth_users
                WHERE username = CAST(:username AS VARCHAR)
            )
            """
        ).bindparams(
            sa.bindparam("username", type_=sa.String(length=255)),
            sa.bindparam("password_hash", type_=sa.String(length=255)),
        ),
        {"username": ADMIN_LOGIN, "password_hash": ADMIN_PASSWORD_HASH},
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO auth_user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM auth_users u
            CROSS JOIN auth_roles r
            WHERE u.username = CAST(:username AS VARCHAR)
              AND r.name = CAST(:role_name AS VARCHAR)
              AND NOT EXISTS (
                    SELECT 1
                    FROM auth_user_roles ur
                    WHERE ur.user_id = u.id
                      AND ur.role_id = r.id
              )
            """
        ).bindparams(
            sa.bindparam("username", type_=sa.String(length=255)),
            sa.bindparam("role_name", type_=sa.String(length=255)),
        ),
        {"username": ADMIN_LOGIN, "role_name": SUPER_ADMIN_ROLE},
    )

    module_stmt = sa.text(
        """
        INSERT INTO auth_role_modules (role_id, module_id)
        SELECT r.id, CAST(:module_id AS VARCHAR)
        FROM auth_roles r
        WHERE r.name = CAST(:role_name AS VARCHAR)
          AND EXISTS (
                SELECT 1
                FROM platform_modules pm
                WHERE pm.id = CAST(:module_id AS VARCHAR)
          )
          AND NOT EXISTS (
                SELECT 1
                FROM auth_role_modules arm
                WHERE arm.role_id = r.id
                  AND arm.module_id = CAST(:module_id AS VARCHAR)
          )
        """
    ).bindparams(
        sa.bindparam("role_name", type_=sa.String(length=255)),
        sa.bindparam("module_id", type_=sa.String(length=64)),
    )

    permission_stmt = sa.text(
        """
        INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
        SELECT r.id, CAST(:module_id AS VARCHAR), CAST(:permission AS VARCHAR), true
        FROM auth_roles r
        WHERE r.name = CAST(:role_name AS VARCHAR)
          AND EXISTS (
                SELECT 1
                FROM platform_modules pm
                WHERE pm.id = CAST(:module_id AS VARCHAR)
          )
          AND NOT EXISTS (
                SELECT 1
                FROM auth_role_module_permissions p
                WHERE p.role_id = r.id
                  AND p.module_id = CAST(:module_id AS VARCHAR)
                  AND p.permission = CAST(:permission AS VARCHAR)
          )
        """
    ).bindparams(
        sa.bindparam("role_name", type_=sa.String(length=255)),
        sa.bindparam("module_id", type_=sa.String(length=64)),
        sa.bindparam("permission", type_=sa.String(length=64)),
    )

    for module_id in MODULES:
        bind.execute(module_stmt, {"role_name": SUPER_ADMIN_ROLE, "module_id": module_id})

    for module_id, permission in PERMISSIONS:
        bind.execute(
            permission_stmt,
            {
                "role_name": SUPER_ADMIN_ROLE,
                "module_id": module_id,
                "permission": permission,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_module_permissions
            WHERE role_id = (SELECT id FROM auth_roles WHERE name = CAST(:role_name AS VARCHAR))
              AND (
                (module_id = 'admin' AND permission = 'admin.view')
                OR
                (module_id = 'employees' AND permission IN (
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
                    'employees.view'
                ))
              )
            """
        ).bindparams(sa.bindparam("role_name", type_=sa.String(length=255))),
        {"role_name": SUPER_ADMIN_ROLE},
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_modules
            WHERE role_id = (SELECT id FROM auth_roles WHERE name = CAST(:role_name AS VARCHAR))
              AND module_id IN ('admin', 'employees')
            """
        ).bindparams(sa.bindparam("role_name", type_=sa.String(length=255))),
        {"role_name": SUPER_ADMIN_ROLE},
    )

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_user_roles
            WHERE user_id = (SELECT id FROM auth_users WHERE username = CAST(:username AS VARCHAR))
              AND role_id = (SELECT id FROM auth_roles WHERE name = CAST(:role_name AS VARCHAR))
            """
        ).bindparams(
            sa.bindparam("username", type_=sa.String(length=255)),
            sa.bindparam("role_name", type_=sa.String(length=255)),
        ),
        {"username": ADMIN_LOGIN, "role_name": SUPER_ADMIN_ROLE},
    )
