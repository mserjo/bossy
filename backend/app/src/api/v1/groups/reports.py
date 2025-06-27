# backend/app/src/api/v1/groups/reports.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для отримання звітів по групі API v1.

Цей модуль надає API для адміністраторів групи (або інших авторизованих ролей)
для генерації та отримання різноманітних звітів, що стосуються активності
та стану конкретної групи. Наприклад:
- Звіт по активності учасників.
- Звіт по виконаних завданнях.
- Звіт по нарахованих/витрачених бонусах.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from typing import Dict, Any, Optional # Для відповіді зі звітом та параметрів
from pydantic import BaseModel # Для тимчасових схем

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.reports.request import GroupReportRequestSchema # Припускаємо, що така схема існує
from backend.app.src.schemas.reports.response import ReportResponseSchema # Загальна схема відповіді для звіту
from backend.app.src.services.reports.report_service import ReportService # Загальний сервіс звітів
from backend.app.src.api.dependencies import DBSession
from backend.app.src.api.v1.groups.groups import group_admin_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Тимчасова схема, якщо GroupReportRequestSchema ще не визначена детально
class TempGroupReportParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    user_ids: Optional[List[int]] = None
    # ... інші специфічні для групових звітів параметри


@router.post(
    "/{report_code}", # report_code - унікальний код типу звіту для групи
    response_model=ReportResponseSchema,
    tags=["Groups", "Group Reports"],
    summary="Згенерувати та отримати звіт по групі"
)
async def generate_and_get_group_specific_report(
    group_id: int = Path(..., description="ID групи"),
    report_code: str = Path(..., description="Код типу звіту, напр. 'group_user_activity', 'group_task_summary'"),
    params: Optional[TempGroupReportParams] = Body(None, description="Параметри для генерації звіту"), # Використовуємо тимчасову або реальну схему
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
):
    """
    Генерує та повертає вказаний тип звіту для конкретної групи.
    Доступно лише адміністраторам цієї групи.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує звіт типу '{report_code}' для групи ID {group_id}."
        f" Параметри: {params.model_dump_json(exclude_none=True) if params else 'немає'}."
    )

    report_service = ReportService(db_session)
    try:
        # ReportService повинен мати метод, що обробляє group_id
        report_data = await report_service.generate_group_report(
            report_code=report_code,
            group_id=group_id,
            params=params, # Передаємо Pydantic модель або словник
            requesting_user_id=current_admin.id
        )
        if not report_data: # Якщо сервіс повертає None при помилці або відсутності даних
            # Це може бути нормально, якщо для звіту немає даних, тоді сервіс має повернути відповідну структуру
            logger.warning(f"Не вдалося згенерувати звіт '{report_code}' для групи {group_id} або дані відсутні.")
            # Відповідь залежить від очікуваної поведінки - 404 чи 200 з порожніми даними
            # Припустимо, що ReportResponseSchema може обробити порожні дані
            # Якщо ж це помилка генерації, сервіс мав би кинути виняток.
            # Для прикладу, якщо звіт не знайдено:
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Тип звіту '{report_code}' не підтримується або дані відсутні.")
            # Поки що повернемо порожній успішний звіт, якщо сервіс так може повернути
            from datetime import datetime
            return ReportResponseSchema(
                report_type=report_code,
                title=f"Звіт: {report_code} (дані відсутні)",
                generated_at=datetime.utcnow().isoformat(),
                parameters_used=params.model_dump(exclude_none=True) if params else {},
                data={} # Порожні дані
            )

        return report_data # report_data має бути екземпляром ReportResponseSchema
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, невірні параметри
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при генерації звіту '{report_code}' для групи {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при генерації звіту.")

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
# з префіксом /{group_id}/reports
