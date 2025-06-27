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
from pydantic import BaseModel
from datetime import datetime # Для generated_at

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.reports.request import ReportRequestSchema, GroupReportParamsSchema # Реальні схеми
from backend.app.src.schemas.reports.response import ReportResponseSchema, UserActivityReportDataSchema # Реальні схеми
from backend.app.src.services.reports.report_service import ReportService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission # Для звітів по групі
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /reports вже встановлено в v1/router.py

@router.post(
    "/generate/{report_code}",
    response_model=ReportResponseSchema,
    tags=["Reports"],
    summary="Запит на генерацію та отримання звіту"
)
async def generate_and_get_report_endpoint(
    report_code: str = Path(..., description="Код типу звіту, напр. 'system_user_activity', 'group_bonus_flow'"),
    params: Optional[ReportRequestSchema] = Body(None, description="Загальні параметри для генерації звіту (період тощо)"),
    # Для звітів, що вимагають прав суперкористувача:
    # current_super_user: Optional[UserModel] = Depends(CurrentSuperuser) # Якщо потрібен тільки для певних звітів
    # Для звітів, що вимагають прав адміна групи (передається group_id в params або шляху):
    # group_admin_check: Optional[dict] = Depends(group_admin_permission) # Якщо звіт завжди по групі
    current_user: UserModel = Depends(CurrentActiveUser), # Загальна перевірка активного користувача
    db_session: DBSession = Depends(),
):
    """
    Генерує та повертає вказаний тип звіту на основі наданих параметрів.
    Права доступу до звіту перевіряються всередині сервісу на основі типу звіту,
    параметрів (напр. group_id) та ID поточного користувача.
    """
    logger.info(
        f"Користувач {current_user.email} запитує генерацію звіту типу '{report_code}'. "
        f"Параметри: {params.model_dump_json(exclude_none=True) if params else 'немає'}."
    )

    report_service = ReportService(db_session)
    try:
        # ReportService.generate_report має перевірити права доступу всередині
        # на основі report_code, params (напр. group_id) та current_user.id
        report_response_data = await report_service.generate_report(
            report_code=report_code,
            params=params,
            requesting_user=current_user # Передаємо всю модель користувача для перевірки прав
        )

        if not report_response_data: # Якщо сервіс повертає None (наприклад, звіт не знайдено або немає даних)
            # Залежно від логіки сервісу, це може бути нормально (немає даних для звіту)
            # або помилка (невірний report_code). Сервіс міг би кинути HTTPException.
            logger.warning(f"Звіт '{report_code}' не згенеровано або дані відсутні для користувача {current_user.email}.")
            # Повернемо відповідь, що даних немає, якщо це не помилка типу звіту
            return ReportResponseSchema(
                report_type=report_code,
                title=f"Звіт: {report_code} (дані відсутні або тип звіту не знайдено)",
                generated_at=datetime.utcnow().isoformat(),
                parameters_used=params.model_dump(exclude_none=True) if params else {},
                data={} # Порожні дані
            )
            # Або якщо тип звіту не знайдено:
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Тип звіту '{report_code}' не підтримується.")

        return report_response_data # report_response_data має бути екземпляром ReportResponseSchema

    except HTTPException as e: # Якщо сервіс кинув помилку прав доступу або валідації
        raise e
    except ValueError as ve: # Наприклад, невірні параметри звіту
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при генерації звіту '{report_code}': {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при генерації звіту.")

# Ендпоінти для звітів по групі можна також розмістити в groups/reports.py
# Якщо вони тут, то group_id має бути частиною шляху або параметрів params.

@router.post(
    "/groups/{group_id}/{report_code}", # Більш явний шлях для групових звітів
    response_model=ReportResponseSchema,
    tags=["Reports", "Group Reports"],
    summary="Звіт по конкретній групі"
)
async def get_specific_group_report(
    group_id: int = Path(..., description="ID групи"),
    report_code: str = Path(..., description="Код типу звіту для групи, напр. 'user_activity', 'task_summary'"),
    params: Optional[GroupReportParamsSchema] = Body(None, description="Специфічні параметри для звіту по групі"),
    group_admin_check: dict = Depends(group_admin_permission), # Перевірка, що користувач є адміном групи
    db_session: DBSession = Depends(),
):
    current_admin: UserModel = group_admin_check["current_user"]
    # Перевірка, чи group_id з шляху збігається з тим, що в admin_check (якщо є)
    # зазвичай group_admin_permission вже використовує group_id з шляху.

    logger.info(
        f"Адміністратор {current_admin.email} запитує звіт '{report_code}' для групи ID {group_id}. "
        f"Параметри: {params.model_dump_json(exclude_none=True) if params else 'немає'}."
    )

    report_service = ReportService(db_session)
    try:
        # Передаємо group_id явно, оскільки він є частиною шляху
        # params може містити додаткові фільтри, як період
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


# Роутер буде підключений в backend/app/src/api/v1/reports/__init__.py
# з префіксом /reports
