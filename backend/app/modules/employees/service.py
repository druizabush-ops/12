from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.security import hash_password
from app.modules.auth.service import get_user_by_id
from app.modules.employees.models import (
    EmployeeRole,
    Group,
    Organization,
    Permission,
    Position,
    PositionRole,
    RolePermission,
    UserOrganization,
    UserPosition,
)
from app.modules.employees.schemas import OrgTreeNode


def _raise_404(entity: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity}_not_found")


def _ensure_user_org(db: Session, user_id: int, organization_id: int) -> None:
    exists = db.scalar(select(UserOrganization.id).where(UserOrganization.user_id == user_id, UserOrganization.organization_id == organization_id))
    if not exists:
        raise HTTPException(status_code=400, detail="user_not_in_organization")


def _ensure_position_cycle_free(db: Session, position_id: int, manager_position_id: int | None) -> None:
    if manager_position_id is None:
        return
    if manager_position_id == position_id:
        raise HTTPException(status_code=400, detail="self_reference_manager_position")

    current = manager_position_id
    visited: set[int] = set()
    while current is not None:
        if current == position_id:
            raise HTTPException(status_code=400, detail="manager_position_cycle")
        if current in visited:
            raise HTTPException(status_code=400, detail="manager_position_cycle")
        visited.add(current)
        current = db.scalar(select(Position.manager_position_id).where(Position.id == current))


def list_users(db: Session, search: str | None, include_archived: bool, organization_id: int | None):
    query = select(User)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(or_(func.lower(User.full_name).like(like), func.lower(User.username).like(like)))
    if not include_archived:
        query = query.where(User.is_archived == False)  # noqa: E712
    users = list(db.scalars(query.order_by(User.id.desc())))

    if organization_id is not None:
        user_ids = set(db.scalars(select(UserOrganization.user_id).where(UserOrganization.organization_id == organization_id)))
        users = [u for u in users if u.id in user_ids]
    return users


def create_employee_user(db: Session, payload) -> User:
    if db.scalar(select(User.id).where(User.username == payload.login)):
        raise HTTPException(status_code=400, detail="login_exists")

    user = User(
        username=payload.login,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=True,
        is_archived=False,
    )
    db.add(user)
    db.flush()

    for organization_id in payload.organization_ids:
        db.add(UserOrganization(user_id=user.id, organization_id=organization_id, is_active=True))

    for position_id in payload.position_ids:
        position = db.get(Position, position_id)
        if not position:
            _raise_404("position")
        _ensure_user_org(db, user.id, position.organization_id)
        db.add(UserPosition(user_id=user.id, position_id=position_id))

    db.commit()
    db.refresh(user)
    return user


def update_employee_user(db: Session, user_id: int, payload) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        _raise_404("user")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.organization_ids is not None:
        db.execute(delete(UserOrganization).where(UserOrganization.user_id == user_id))
        for organization_id in payload.organization_ids:
            db.add(UserOrganization(user_id=user_id, organization_id=organization_id, is_active=True))

    if payload.position_ids is not None:
        db.execute(delete(UserPosition).where(UserPosition.user_id == user_id))
        for position_id in payload.position_ids:
            position = db.get(Position, position_id)
            if not position:
                _raise_404("position")
            _ensure_user_org(db, user_id, position.organization_id)
            db.add(UserPosition(user_id=user_id, position_id=position_id))

    db.commit()
    db.refresh(user)
    return user


def set_user_password(db: Session, user_id: int, new_password: str) -> None:
    user = get_user_by_id(db, user_id)
    if not user:
        _raise_404("user")
    user.hashed_password = hash_password(new_password)
    db.commit()


def list_permissions(db: Session):
    return list(db.scalars(select(Permission).order_by(Permission.module, Permission.action)))


def calc_user_permissions(db: Session, user_id: int, organization_id: int) -> dict[str, bool]:
    role_codes = db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(PositionRole, PositionRole.role_id == RolePermission.role_id)
        .join(Position, Position.id == PositionRole.position_id)
        .join(UserPosition, UserPosition.position_id == Position.id)
        .where(UserPosition.user_id == user_id, Position.organization_id == organization_id)
    ).all()
    result: dict[str, bool] = {}
    for (code,) in role_codes:
        result[code] = True
    return result


def calc_user_managers(db: Session, user_id: int, organization_id: int):
    positions = db.execute(
        select(Position.id, Position.name, Position.manager_position_id, Group.head_user_id)
        .join(UserPosition, UserPosition.position_id == Position.id)
        .join(Group, Group.id == Position.group_id)
        .where(UserPosition.user_id == user_id, Position.organization_id == organization_id)
    ).all()
    result = []
    for pos_id, pos_name, manager_pos_id, head_user_id in positions:
        manager_users = []
        if manager_pos_id:
            manager_users = list(
                db.execute(
                    select(User.id, User.full_name)
                    .join(UserPosition, UserPosition.user_id == User.id)
                    .where(UserPosition.position_id == manager_pos_id)
                ).all()
            )
        elif head_user_id:
            head = db.get(User, head_user_id)
            if head:
                manager_users = [(head.id, head.full_name)]
        result.append({"position_id": pos_id, "position_name": pos_name, "managers": [{"id": m[0], "full_name": m[1]} for m in manager_users]})
    return result


def build_org_tree(db: Session, organization_id: int, include_archived: bool) -> list[OrgTreeNode]:
    groups = list(db.scalars(select(Group).where(Group.organization_id == organization_id)))
    positions = list(db.scalars(select(Position).where(Position.organization_id == organization_id)))
    users_by_position: dict[int, list[tuple[int, str, bool]]] = defaultdict(list)
    rows = db.execute(
        select(UserPosition.position_id, User.id, User.full_name, User.is_archived)
        .join(User, User.id == UserPosition.user_id)
        .join(Position, Position.id == UserPosition.position_id)
        .where(Position.organization_id == organization_id)
    ).all()
    for position_id, user_id, full_name, is_archived in rows:
        users_by_position[position_id].append((user_id, full_name, is_archived))

    group_children: dict[int | None, list[Group]] = defaultdict(list)
    for group in groups:
        if include_archived or not group.is_archived:
            group_children[group.parent_group_id].append(group)

    position_by_group: dict[int, list[Position]] = defaultdict(list)
    for position in positions:
        if include_archived or not position.is_archived:
            position_by_group[position.group_id].append(position)

    def render_group(group: Group) -> OrgTreeNode:
        position_nodes: list[OrgTreeNode] = []
        sorted_positions = sorted(position_by_group.get(group.id, []), key=lambda p: (0 if p.manager_position_id is None else 1, p.sort_order, p.name))
        for position in sorted_positions:
            user_nodes = [
                OrgTreeNode(id=f"user:{uid}:pos:{position.id}", type="user", title=full_name, archived=arch, children=[])
                for uid, full_name, arch in users_by_position.get(position.id, [])
            ]
            position_nodes.append(
                OrgTreeNode(id=f"position:{position.id}", type="position", title=position.name, archived=position.is_archived, children=user_nodes)
            )
        subgroup_nodes = [render_group(sub) for sub in sorted(group_children.get(group.id, []), key=lambda g: (g.sort_order, g.name))]
        children = position_nodes + subgroup_nodes
        return OrgTreeNode(id=f"group:{group.id}", type="group", title=group.name, archived=group.is_archived, children=children)

    return [render_group(group) for group in sorted(group_children.get(None, []), key=lambda g: (g.sort_order, g.name))]
