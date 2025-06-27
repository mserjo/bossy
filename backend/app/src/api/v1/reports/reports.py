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
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel # Для тимчасових схем параметрів та відповідей

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати реальні схеми для параметрів запиту звітів та відповідей, коли вони будуть готові.
# from backend.app.src.schemas.reports.request import ReportRequestSchema, GroupReportParamsSchema
# from backend.app.src.schemas.reports.response import ReportResponseSchema, UserActivityReportSchema
# TODO: Імпортувати сервіс ReportService.
# from backend.app.src.services.reports.report_service import ReportService
# TODO: Імпортувати залежності (DBSession, CurrentSuperuser, group_admin_permission).
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser # Приклади
from backend.app.src.api.v1.groups.groups import group_admin_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Тимчасова схема для параметрів звіту (загальна)
class GenericReportParams(BaseModel):
    start_date: Optional[str] = None # Наприклад, "YYYY-MM-DD"
    end_date: Optional[str] = None
    user_ids: Optional[List[int]] = None
    # ... інші можливі параметри

# Тимчасова схема для відповіді звіту (загальна)
class GenericReportResponse(BaseModel):
    report_type: str
    title: str
    generated_at: str # ISO datetime
    parameters_used: Optional[Dict[str, Any]] = None
    data: Any # Може бути списком, словником, залежно від звіту

# Ендпоінти можуть мати префікс /reports
# Або /groups/{group_id}/reports для звітів по групі

@router.post(
    "/generate/{report_code}", # report_code - унікальний код типу звіту
    response_model=GenericReportResponse, # TODO: Замінити на специфічну схему відповіді
    tags=["Reports"],
    summary="Запит на генерацію та отримання звіту (заглушка)"
)
async def generate_and_get_report(
    report_code: str = Path(..., description="Код типу звіту, напр. 'user_activity', 'group_bonus_flow'"),
    params: GenericReportParams = Body(None, description="Параметри для генерації звіту"),
    # current_user: UserModel = Depends(CurrentActiveUser), # Для перевірки прав доступу до звіту
    # db_session: DBSession = Depends(),
):
    """
    Генерує та повертає вказаний тип звіту на основі наданих параметрів.
    Права доступу до звіту перевіряються на основі типу звіту та користувача.
    """
    logger.info(
        f"Запит на генерацію звіту типу '{report_code}' "
        f"(параметри: {params.model_dump_json() if params else 'немає'}) "
        # f"від користувача {current_user.email} (заглушка)."
    )

    # TODO: Реальна логіка з ReportService
    # 1. Перевірити права користувача на генерацію цього типу звіту (report_code)
    #    з цими параметрами (наприклад, чи має доступ до групи, якщо звіт по групі).
    # 2. Викликати ReportService для генерації даних.
    # report_service = ReportService(db_session)
    # report_data = await report_service.generate_report(
    #     report_code=report_code,
    #     params=params,
    #     requesting_user_id=current_user.id
    # )
    # if not report_data:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Звіт не може бути згенерований або дані відсутні.")

    # Заглушка відповіді
    from datetime import datetime
    return GenericReportResponse(
        report_type=report_code,
        title=f"Звіт: {report_code.replace('_', ' ').title()}",
        generated_at=datetime.utcnow().isoformat(),
        parameters_used=params.model_dump() if params else {},
        data={"summary": f"Це заглушка даних для звіту '{report_code}'.", "details": ["Деталь 1", "Деталь 2"]}
    )

# Приклад специфічного ендпоінту для звіту по групі
@router.post(
    "/groups/{group_id}/activity-summary",
    response_model=GenericReportResponse, # TODO: Замінити на специфічну схему
    tags=["Reports", "Group Reports"],
    summary="Звіт по активності в групі (заглушка)"
)
async def get_group_activity_summary_report(
    group_id: int = Path(..., description="ID групи"),
    params: GenericReportParams = Body(None, description="Параметри для звіту (напр., період)"),
    group_with_admin_rights: dict = Depends(group_admin_permission), # Лише адмін групи
    # db_session: DBSession = Depends(),
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    report_code = "group_activity_summary"
    logger.info(
        f"Адмін {current_admin.email} запитує звіт '{report_code}' для групи ID {group_id} "
        f"(параметри: {params.model_dump_json() if params else 'немає'}) (заглушка)."
    )
    # TODO: Логіка виклику ReportService
    from datetime import datetime
    return GenericReportResponse(
        report_type=report_code,
        title=f"Звіт по активності для групи {group_id}",
        generated_at=datetime.utcnow().isoformat(),
        parameters_used=params.model_dump() if params else {},
        data={"total_active_users": 10, "tasks_completed_this_week": 25, "group_id": group_id}
    )

# Роутер буде підключений в backend/app/src/api/v1/reports/__init__.py
