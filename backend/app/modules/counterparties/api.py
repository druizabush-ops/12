from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.counterparties.schemas import (
    CounterpartyAutoTaskRuleCreatePayload,
    CounterpartyAutoTaskRuleDto,
    CounterpartyAutoTaskRulePatchPayload,
    CounterpartyDto,
    CounterpartyFolderCreatePayload,
    CounterpartyFolderDto,
    CounterpartyFolderUpdatePayload,
    CounterpartyTaskCreatorSettingsDto,
    CounterpartyTaskCreatorSettingsPayload,
    CounterpartyUpsertPayload,
)
from app.modules.counterparties.service import (
    archive_counterparty,
    create_auto_task_rule,
    create_counterparty,
    create_folder,
    delete_auto_task_rule,
    delete_folder,
    get_counterparty_dto,
    get_task_creator_settings,
    list_auto_task_rules,
    list_counterparties,
    list_folders,
    pause_auto_task_rule,
    resume_auto_task_rule,
    stop_auto_task_rule,
    update_auto_task_rule,
    update_counterparty,
    update_folder,
    update_task_creator_settings,
)

router = APIRouter(prefix="/counterparties", tags=["counterparties"], dependencies=[Depends(get_current_user)])


@router.get("/settings", response_model=CounterpartyTaskCreatorSettingsDto)
def get_settings(db: Session = Depends(get_db)) -> CounterpartyTaskCreatorSettingsDto:
    return get_task_creator_settings(db)


@router.patch("/settings", response_model=CounterpartyTaskCreatorSettingsDto)
def patch_settings(payload: CounterpartyTaskCreatorSettingsPayload, db: Session = Depends(get_db)) -> CounterpartyTaskCreatorSettingsDto:
    return update_task_creator_settings(db, payload)


@router.get("/folders", response_model=list[CounterpartyFolderDto])
def get_folders(db: Session = Depends(get_db)) -> list[CounterpartyFolderDto]:
    return list_folders(db)


@router.post("/folders", response_model=CounterpartyFolderDto, status_code=status.HTTP_201_CREATED)
def post_folder(payload: CounterpartyFolderCreatePayload, db: Session = Depends(get_db)) -> CounterpartyFolderDto:
    return create_folder(db, payload)


@router.patch("/folders/{folder_id}", response_model=CounterpartyFolderDto)
def patch_folder(folder_id: int, payload: CounterpartyFolderUpdatePayload, db: Session = Depends(get_db)) -> CounterpartyFolderDto:
    try:
        return update_folder(db, folder_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Папка не найдена")


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_folder(folder_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        delete_folder(db, folder_id)
    except ValueError as exc:
        code = str(exc)
        if code == "folder_not_found":
            raise HTTPException(status_code=404, detail="Папка не найдена")
        if code == "folder_not_empty":
            raise HTTPException(status_code=400, detail="Нельзя удалить папку, пока в ней есть контрагенты или вложенные элементы")
        raise HTTPException(status_code=400, detail=code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.get("/{counterparty_id}/auto-tasks", response_model=list[CounterpartyAutoTaskRuleDto])
def get_rules(counterparty_id: int, db: Session = Depends(get_db)) -> list[CounterpartyAutoTaskRuleDto]:
    try:
        return list_auto_task_rules(db, counterparty_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.post("/{counterparty_id}/auto-tasks", response_model=CounterpartyAutoTaskRuleDto, status_code=status.HTTP_201_CREATED)
def post_rule(counterparty_id: int, payload: CounterpartyAutoTaskRuleCreatePayload, db: Session = Depends(get_db)) -> CounterpartyAutoTaskRuleDto:
    try:
        return create_auto_task_rule(db, counterparty_id, payload)
    except ValueError as exc:
        if str(exc) == "counterparty_not_found":
            raise HTTPException(status_code=404, detail="Контрагент не найден")
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{counterparty_id}/auto-tasks/{rule_id}", response_model=CounterpartyAutoTaskRuleDto)
def patch_rule(
    counterparty_id: int,
    rule_id: int,
    payload: CounterpartyAutoTaskRulePatchPayload,
    action: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CounterpartyAutoTaskRuleDto:
    try:
        return update_auto_task_rule(db, counterparty_id, rule_id, payload, action)
    except ValueError as exc:
        code = str(exc)
        if code in {"counterparty_not_found", "rule_not_found"}:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        raise HTTPException(status_code=400, detail=code)


@router.post("/{counterparty_id}/auto-tasks/{rule_id}/pause", response_model=CounterpartyAutoTaskRuleDto)
def post_pause_rule(counterparty_id: int, rule_id: int, db: Session = Depends(get_db)) -> CounterpartyAutoTaskRuleDto:
    try:
        return pause_auto_task_rule(db, counterparty_id, rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Правило не найдено")


@router.post("/{counterparty_id}/auto-tasks/{rule_id}/resume", response_model=CounterpartyAutoTaskRuleDto)
def post_resume_rule(counterparty_id: int, rule_id: int, db: Session = Depends(get_db)) -> CounterpartyAutoTaskRuleDto:
    try:
        return resume_auto_task_rule(db, counterparty_id, rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Правило не найдено")


@router.post("/{counterparty_id}/auto-tasks/{rule_id}/stop", response_model=CounterpartyAutoTaskRuleDto)
def post_stop_rule(counterparty_id: int, rule_id: int, db: Session = Depends(get_db)) -> CounterpartyAutoTaskRuleDto:
    try:
        return stop_auto_task_rule(db, counterparty_id, rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Правило не найдено")


@router.delete("/{counterparty_id}/auto-tasks/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(counterparty_id: int, rule_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        delete_auto_task_rule(db, counterparty_id, rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
