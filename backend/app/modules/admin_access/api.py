from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.admin_access.schemas import (
    ChangeImpactDto,
    ModuleAccessPayload,
    PermissionsDto,
    PermissionsUpdatePayload,
    RoleCreatePayload,
    RoleDto,
    SessionActionPayload,
    UserRolesDto,
    UserRolesUpdatePayload,
)
from app.modules.admin_access.service import (
    create_role,
    delete_role,
    get_role_module_permissions,
    list_affected_users,
    list_platform_modules,
    list_roles,
    list_users_with_roles,
    update_module_access,
    update_role_module_permissions,
    update_user_roles,
    user_can_manage_access,
)
from app.modules.auth.service import get_db

router = APIRouter(prefix="/admin/access", tags=["admin_access"], dependencies=[Depends(get_current_user)])


def _require_manage_access(db: Session, current_user: UserContext) -> None:
    if not user_can_manage_access(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")


@router.get("/roles", response_model=list[RoleDto])
def get_roles(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)) -> list[RoleDto]:
    _require_manage_access(db, current_user)
    return list_roles(db)


@router.post("/roles", response_model=RoleDto, status_code=status.HTTP_201_CREATED)
def post_role(
    payload: RoleCreatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoleDto:
    _require_manage_access(db, current_user)
    try:
        return create_role(db, payload.name)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Роль уже существует")


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role(
    role_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _require_manage_access(db, current_user)
    try:
        delete_role(db, role_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")


@router.get("/modules")
def get_modules(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _require_manage_access(db, current_user)
    return list_platform_modules(db)


@router.patch("/roles/{role_id}/modules/{module_id}", response_model=ChangeImpactDto)
def patch_module_access(
    role_id: int,
    module_id: str,
    payload: ModuleAccessPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeImpactDto:
    _require_manage_access(db, current_user)
    try:
        update_module_access(db, role_id, module_id, payload.has_access)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль или модуль не найдены")
    users = list_affected_users(db, [role_id])
    return ChangeImpactDto(message="Изменения затрагивают активных пользователей", affected_users=users)


@router.get("/roles/{role_id}/modules/{module_id}/permissions", response_model=PermissionsDto)
def get_permissions(
    role_id: int,
    module_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PermissionsDto:
    _require_manage_access(db, current_user)
    try:
        return get_role_module_permissions(db, role_id, module_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль или модуль не найдены")


@router.put("/roles/{role_id}/modules/{module_id}/permissions", response_model=ChangeImpactDto)
def put_permissions(
    role_id: int,
    module_id: str,
    payload: PermissionsUpdatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeImpactDto:
    _require_manage_access(db, current_user)
    try:
        update_role_module_permissions(db, role_id, module_id, payload.permissions)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль или модуль не найдены")
    users = list_affected_users(db, [role_id])
    return ChangeImpactDto(message="Изменения затрагивают активных пользователей", affected_users=users)


@router.get("/users", response_model=list[UserRolesDto])
def get_users(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)) -> list[UserRolesDto]:
    _require_manage_access(db, current_user)
    return list_users_with_roles(db)


@router.put("/users/{user_id}/roles", response_model=ChangeImpactDto)
def put_user_roles(
    user_id: int,
    payload: UserRolesUpdatePayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeImpactDto:
    _require_manage_access(db, current_user)
    try:
        update_user_roles(db, user_id, payload.role_ids)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")
    users = list_affected_users(db, payload.role_ids)
    return ChangeImpactDto(message="Изменения затрагивают активных пользователей", affected_users=users)


@router.post("/session-actions", status_code=status.HTTP_202_ACCEPTED)
def post_session_action(
    payload: SessionActionPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _require_manage_access(db, current_user)
    if payload.mode not in {"now", "5m"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестный режим")
    if payload.mode == "now":
        return {"status": "accepted", "message": "Затронутые пользователи должны перезайти сейчас"}
    return {
        "status": "accepted",
        "message": "Для продолжения работы, пожалуйста, перезайдите в систему в течение 5 минут",
    }
