# backend/app/src/api/v1/reports/reports.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для генерації та отримання звітів API v1.

Цей модуль надає API для запиту різних типів звітів, наприклад:
- Активність користувачів.
- Популярність завдань/нагород.
- Динаміка накопичення бонусів.
- Системні звіти (для суперкористувача).
- Звіти по конкретній групі (для адміністратора групи).
- Персональні звіти для користувачів.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.reports.request import ReportRequestSchema, GroupReportParamsSchema
from backend.app.src.schemas.reports.response import ReportResponseSchema, AvailableReportSchema
from backend.app.src.services.reports.report_service import ReportService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /reports вже встановлено в v1/router.py

@router.get(
    "/available-reports",
    response_model=List[AvailableReportSchema],
    tags=["Reports"],
    summary="Отримати список доступних типів звітів"
)
async def list_available_reports(
    # current_user: UserModel = Depends(CurrentActiveUser), # Для фільтрації звітів за правами
    db_session: DBSession = Depends()
):
    """
    Повертає список всіх доступних для генерації типів звітів,
    їх опис та необхідні параметри.
    """
    report_service = ReportService(db_session)
    # Сервіс може фільтрувати звіти на основі прав поточного користувача, якщо current_user передається
    available_reports = await report_service.get_available_reports_list(user=None) # Передати current_user для фільтрації за правами
    return available_reports

@router.post(
    "/generate/{report_code}",
    response_model=ReportResponseSchema,
    tags=["Reports"],
    summary="Запит на генерацію та отримання звіту"
)
async def generate_and_get_report_endpoint(
    report_code: str = Path(..., description="Код типу звіту, напр. 'system_user_activity', 'group_bonus_flow', 'my_activity_summary'"),
    params: Optional[ReportRequestSchema] = Body(None, description="Загальні параметри для генерації звіту (період тощо)"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
):
    logger.info(
        f"Користувач {current_user.email} запитує генерацію звіту типу '{report_code}'. "
        f"Параметри: {params.model_dump_json(exclude_none=True) if params else 'немає'}."
    )
    report_service = ReportService(db_session)
    try:
        report_response_data = await report_service.generate_report(
            report_code=report_code,
            params=params,
            requesting_user=current_user
        )
        if not report_response_data:
             return ReportResponseSchema(
                report_type=report_code,
                title=f"Звіт: {report_code} (дані відсутні або тип звіту не знайдено)",
                generated_at=datetime.utcnow().isoformat(),
                parameters_used=params.model_dump(exclude_none=True) if params else {},
                data={}
            )
        return report_response_data
    except HTTPException as e:
        raise e
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при генерації звіту '{report_code}': {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при генерації звіту.")

@router.post(
    "/groups/{group_id}/{report_code}",
    response_model=ReportResponseSchema,
    tags=["Reports", "Group Reports"],
    summary="Звіт по конкретній групі"
)
async def get_specific_group_report(
    group_id: int = Path(..., description="ID групи"),
    report_code: str = Path(..., description="Код типу звіту для групи, напр. 'user_activity', 'task_summary'"),
    params: Optional[GroupReportParamsSchema] = Body(None, description="Специфічні параметри для звіту по групі"),
    group_admin_check: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
):
    current_admin: UserModel = group_admin_check["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує звіт '{report_code}' для групи ID {group_id}. "
        f"Параметри: {params.model_dump_json(exclude_none=True) if params else 'немає'}."
    )
    report_service = ReportService(db_session)
    try:
        report_response_data = await report_service.generate_group_specific_report(
            report_code=report_code,
            group_id=group_id,
            params=params,
            requesting_user=current_admin
        )
        if not report_response_data:
             return ReportResponseSchema(
                report_type=report_code,
                title=f"Звіт: {report_code} для групи {group_id} (дані відсутні або тип звіту не знайдено)",
                generated_at=datetime.utcnow().isoformat(),
                parameters_used=params.model_dump(exclude_none=True) if params else {},
                data={}
            )
        return report_response_data
    except HTTPException as e:
        raise e
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при генерації звіту '{report_code}' для групи {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")
