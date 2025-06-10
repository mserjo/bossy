# backend/app/src/api/v1/groups/reports.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict # Для гнучкої відповіді звіту

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.services.groups.report import GroupReportService # Майбутній сервіс для звітів
# from app.src.schemas.groups.report import GroupActivityReportResponse # Майбутня схема для звіту

router = APIRouter()

@router.get(
    "/activity", # Шлях відносно префіксу, що буде заданий при підключенні (наприклад, /{group_id}/reports)
    response_model=Dict[str, Any],
    summary="Звіт про активність групи (Placeholder)",
    description="""Повертає звіт про активність у вказаній групі.
    Доступно адміністраторам групи або суперюзерам.
    На даний момент цей ендпоінт є концептуальним (placeholder) і повертатиме заглушку."""
)
async def get_group_activity_report(
    group_id: int = Path(..., description="ID групи, для якої потрібен звіт"), # group_id береться з префіксу шляху, який буде /groups/{group_id}/reports
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user)
    # report_service: GroupReportService = Depends() # Коли сервіс буде реалізовано
):
    '''
    Отримує звіт про активність групи.
    - Потрібна перевірка прав: користувач має бути адміністратором групи або суперюзером.
    - Логіка генерації звіту буде в `GroupReportService`.
    '''
    # Перевірка прав (має бути в сервісі або через GroupPermissionsChecker)
    # await GroupPermissionsChecker(db).check_user_can_view_group_reports(user=current_user, group_id=group_id)

    # Логіка отримання звіту з report_service
    # report_data = await report_service.generate_activity_report(group_id=group_id, requesting_user=current_user)
    # if not report_data:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Звіт не знайдено або доступ заборонено.")
    # return report_data

    # Повертаємо заглушку, оскільки реалізація звіту ще не визначена
    return {
        "group_id": group_id,
        "report_type": "activity",
        "status": "Placeholder - Not Implemented",
        "message": "Функціонал звіту про активність групи буде реалізовано пізніше.",
        "data": {
            "total_tasks_completed": "N/A",
            "active_members_count": "N/A",
            "recent_activities": []
        }
    }

# Міркування:
# 1.  Placeholder: Цей файл та ендпоінт є заглушками. Коли вимоги до звітів стануть відомі,
#     будуть додані конкретні Pydantic схеми для відповідей та реалізований `GroupReportService`.
# 2.  URL: Ендпоінт `/activity` буде доступний за шляхом на кшталт `/api/v1/groups/{group_id}/reports/activity`,
#     де префікс `/{group_id}/reports` задається при підключенні цього роутера (`reports_router`)
#     до агрегованого `groups_router` в `groups/__init__.py`.
# 3.  Права доступу: Передбачається, що звіти будуть доступні адміністраторам групи та суперюзерам.
#     Ця логіка буде в сервісі звітів.
# 4.  Коментарі: Українською мовою.
# 5.  Майбутні розширення: Можуть бути додані інші типи звітів (наприклад, фінансові, по залученості тощо)
#     з відповідними ендпоінтами та логікою.
