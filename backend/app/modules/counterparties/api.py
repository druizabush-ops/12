from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.counterparties.schemas import (
    CounterpartyAutoTaskRuleDto,
    CounterpartyAutoTaskRuleUpsertPayload,
    CounterpartyDto,
    CounterpartyFolderCreatePayload,
    CounterpartyFolderDto,
    CounterpartyFolderUpdatePayload,
    CounterpartyUpsertPayload,
)
from app.modules.counterparties.service import (
    archive_counterparty,
    create_auto_task_rule,
    create_counterparty,
    create_folder,
    get_counterparty_dto,
    list_auto_task_rules,
    list_counterparties,
    list_folders,
    update_auto_task_rule,
    update_counterparty,
    update_folder,
)

router = APIRouter(prefix="/counterparties", tags=["counterparties"], dependencies=[Depends(get_current_user)])


@router.get("/folders", response_model=list[CounterpartyFolderDto])
def get_folders(db: Session = Depends(get_db)) -> list[CounterpartyFolderDto]:
    return list_folders(db)


@router.post("/folders", response_model=CounterpartyFolderDto, status_code=status.HTTP_201_CREATED)
def post_folder(payload: CounterpartyFolderCreatePayload, db: Session = Depends(get_db)) -> CounterpartyFolderDto:
    return create_folder(db, payload)


@router.patch("/folders/{folder_id}", response_model=CounterpartyFolderDto)
def patch_folder(
    folder_id: int,
    payload: CounterpartyFolderUpdatePayload,
    db: Session = Depends(get_db),
) -> CounterpartyFolderDto:
    try:
        return update_folder(db, folder_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Папка не найдена")


@router.get("", response_model=list[CounterpartyDto])
def get_counterparties(include_archived: bool = Query(False), db: Session = Depends(get_db)) -> list[CounterpartyDto]:
    return list_counterparties(db, include_archived)


@router.get("/{counterparty_id}", response_model=CounterpartyDto)
def get_counterparty(counterparty_id: int, db: Session = Depends(get_db)) -> CounterpartyDto:
    try:
        return get_counterparty_dto(db, counterparty_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.post("", response_model=CounterpartyDto, status_code=status.HTTP_201_CREATED)
def post_counterparty(payload: CounterpartyUpsertPayload, db: Session = Depends(get_db)) -> CounterpartyDto:
    return create_counterparty(db, payload)


@router.put("/{counterparty_id}", response_model=CounterpartyDto)
def put_counterparty(counterparty_id: int, payload: CounterpartyUpsertPayload, db: Session = Depends(get_db)) -> CounterpartyDto:
    try:
        return update_counterparty(db, counterparty_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.post("/{counterparty_id}/archive", response_model=CounterpartyDto)
def post_archive_counterparty(counterparty_id: int, db: Session = Depends(get_db)) -> CounterpartyDto:
    try:
        return archive_counterparty(db, counterparty_id, True)
    except ValueError:
        raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.post("/{counterparty_id}/restore", response_model=CounterpartyDto)
def post_restore_counterparty(counterparty_id: int, db: Session = Depends(get_db)) -> CounterpartyDto:
    try:
        return archive_counterparty(db, counterparty_id, False)
    except ValueError:
        raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.get("/{counterparty_id}/auto-task-rules", response_model=list[CounterpartyAutoTaskRuleDto])
def get_rules(counterparty_id: int, db: Session = Depends(get_db)) -> list[CounterpartyAutoTaskRuleDto]:
    return list_auto_task_rules(db, counterparty_id)


@router.post("/{counterparty_id}/auto-task-rules", response_model=CounterpartyAutoTaskRuleDto, status_code=status.HTTP_201_CREATED)
def post_rule(
    counterparty_id: int,
    payload: CounterpartyAutoTaskRuleUpsertPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CounterpartyAutoTaskRuleDto:
    try:
        return create_auto_task_rule(db, current_user.id, counterparty_id, payload)
    except ValueError as exc:
        if str(exc) == "counterparty_not_found":
            raise HTTPException(status_code=404, detail="Контрагент не найден")
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{counterparty_id}/auto-task-rules/{rule_id}", response_model=CounterpartyAutoTaskRuleDto)
def put_rule(
    counterparty_id: int,
    rule_id: int,
    payload: CounterpartyAutoTaskRuleUpsertPayload,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CounterpartyAutoTaskRuleDto:
    try:
        return update_auto_task_rule(db, current_user.id, counterparty_id, rule_id, payload)
    except ValueError as exc:
        code = str(exc)
        if code in {"counterparty_not_found", "rule_not_found"}:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        raise HTTPException(status_code=400, detail=code)
