"""Исправляет bootstrap RBAC для SUPER_ADMIN и модуля сотрудников."""

from alembic import op
import sqlalchemy as sa

revision = "0014_rbac_fix"
down_revision = "0013_employees_module"
branch_labels = None
depends_on = None


REQUIRED_PERMISSIONS: tuple[tuple[str, str], ...] = (
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
    ("employees", "employees.view"),
    ("admin", "admin.view"),
)


def _sync_sequence(bind: sa.engine.Connection, table_name: str, column_name: str = "id") -> None:
    stmt = sa.text(
        """
        SELECT setval(
            pg_get_serial_sequence(CAST(:table_name AS TEXT), CAST(:column_name AS TEXT)),
            COALESCE((SELECT MAX(id) FROM {table_name}), 1),
            true
        )
        """.format(table_name=table_name)
    ).bindparams(
        sa.bindparam("table_name", type_=sa.String()),
        sa.bindparam("column_name", type_=sa.String()),
    )
    bind.execute(stmt, {"table_name": table_name, "column_name": column_name})


def upgrade() -> None:
    bind = op.get_bind()

    _sync_sequence(bind, "auth_roles")

    insert_super_admin_role = sa.text(
        """
        INSERT INTO auth_roles (name, can_manage_access)
        SELECT CAST(:name AS VARCHAR), true
        WHERE NOT EXISTS (
            SELECT 1 FROM auth_roles WHERE name = CAST(:name AS VARCHAR)
        )
        """
    ).bindparams(sa.bindparam("name", type_=sa.String()))
    bind.execute(insert_super_admin_role, {"name": "SUPER_ADMIN"})

    super_admin_role_id = bind.scalar(
        sa.text(
            """
            SELECT id
            FROM auth_roles
            WHERE name = CAST(:name AS VARCHAR)
            LIMIT 1
            """
        ).bindparams(sa.bindparam("name", type_=sa.String())),
        {"name": "SUPER_ADMIN"},
    )

    if super_admin_role_id is None:
        raise RuntimeError("Не удалось создать или найти роль SUPER_ADMIN")

    _sync_sequence(bind, "auth_users")

    insert_admin_user = sa.text(
        """
        INSERT INTO auth_users (username, hashed_password)
        SELECT CAST(:username AS VARCHAR), CAST(:password_hash AS VARCHAR)
        WHERE NOT EXISTS (
            SELECT 1 FROM auth_users WHERE username = CAST(:username AS VARCHAR)
        )
        """
    ).bindparams(
        sa.bindparam("username", type_=sa.String()),
        sa.bindparam("password_hash", type_=sa.String()),
    )
    bind.execute(
        insert_admin_user,
        {
            "username": "admin",
            "password_hash": "$2b$12$6L/KwVRtpAkuGiST07XHqOPvuTDn7qrA6gfkhhjVwX.KjdHc9aOSq",
        },
    )

    attach_super_admin_to_admin_login = sa.text(
        """
        INSERT INTO auth_user_roles (user_id, role_id)
        SELECT u.id, CAST(:role_id AS INTEGER)
        FROM auth_users u
        WHERE u.username = CAST(:username AS VARCHAR)
          AND NOT EXISTS (
              SELECT 1
              FROM auth_user_roles ur
              WHERE ur.user_id = u.id
                AND ur.role_id = CAST(:role_id AS INTEGER)
          )
        """
    ).bindparams(
        sa.bindparam("username", type_=sa.String()),
        sa.bindparam("role_id", type_=sa.Integer()),
    )
    bind.execute(
        attach_super_admin_to_admin_login,
        {"username": "admin", "role_id": int(super_admin_role_id)},
    )

    grant_super_admin_all_modules = sa.text(
        """
        INSERT INTO auth_role_modules (role_id, module_id)
        SELECT CAST(:role_id AS INTEGER), pm.id
        FROM platform_modules pm
        WHERE NOT EXISTS (
            SELECT 1
            FROM auth_role_modules arm
            WHERE arm.role_id = CAST(:role_id AS INTEGER)
              AND arm.module_id = pm.id
        )
        """
    ).bindparams(sa.bindparam("role_id", type_=sa.Integer()))
    bind.execute(grant_super_admin_all_modules, {"role_id": int(super_admin_role_id)})

    copy_existing_permissions = sa.text(
        """
        INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
        SELECT CAST(:role_id AS INTEGER), rp.module_id, rp.permission, true
        FROM auth_role_module_permissions rp
        WHERE rp.is_allowed = true
          AND NOT EXISTS (
              SELECT 1
              FROM auth_role_module_permissions target
              WHERE target.role_id = CAST(:role_id AS INTEGER)
                AND target.module_id = rp.module_id
                AND target.permission = rp.permission
          )
        """
    ).bindparams(sa.bindparam("role_id", type_=sa.Integer()))
    bind.execute(copy_existing_permissions, {"role_id": int(super_admin_role_id)})

    add_required_permission = sa.text(
        """
        INSERT INTO auth_role_module_permissions (role_id, module_id, permission, is_allowed)
        SELECT CAST(:role_id AS INTEGER), CAST(:module_id AS VARCHAR), CAST(:permission AS VARCHAR), true
        WHERE EXISTS (
            SELECT 1 FROM platform_modules pm WHERE pm.id = CAST(:module_id AS VARCHAR)
        )
          AND NOT EXISTS (
            SELECT 1
            FROM auth_role_module_permissions rp
            WHERE rp.role_id = CAST(:role_id AS INTEGER)
              AND rp.module_id = CAST(:module_id AS VARCHAR)
              AND rp.permission = CAST(:permission AS VARCHAR)
          )
        """
    ).bindparams(
        sa.bindparam("role_id", type_=sa.Integer()),
        sa.bindparam("module_id", type_=sa.String()),
        sa.bindparam("permission", type_=sa.String()),
    )

    for module_id, permission in REQUIRED_PERMISSIONS:
        bind.execute(
            add_required_permission,
            {
                "role_id": int(super_admin_role_id),
                "module_id": module_id,
                "permission": permission,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()

    super_admin_role_id = bind.scalar(
        sa.text(
            """
            SELECT id
            FROM auth_roles
            WHERE name = CAST(:name AS VARCHAR)
            LIMIT 1
            """
        ).bindparams(sa.bindparam("name", type_=sa.String())),
        {"name": "SUPER_ADMIN"},
    )

    if super_admin_role_id is None:
        return

    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_module_permissions
            WHERE role_id = CAST(:role_id AS INTEGER)
            """
        ).bindparams(sa.bindparam("role_id", type_=sa.Integer())),
        {"role_id": int(super_admin_role_id)},
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM auth_role_modules
            WHERE role_id = CAST(:role_id AS INTEGER)
            """
        ).bindparams(sa.bindparam("role_id", type_=sa.Integer())),
        {"role_id": int(super_admin_role_id)},
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM auth_user_roles
            WHERE role_id = CAST(:role_id AS INTEGER)
            """
        ).bindparams(sa.bindparam("role_id", type_=sa.Integer())),
        {"role_id": int(super_admin_role_id)},
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM auth_roles
            WHERE id = CAST(:role_id AS INTEGER)
            """
        ).bindparams(sa.bindparam("role_id", type_=sa.Integer())),
        {"role_id": int(super_admin_role_id)},
    )
