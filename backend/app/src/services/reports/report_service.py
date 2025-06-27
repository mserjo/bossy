# backend/app/src/services/reports/report_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `ReportService` для управління записами про звіти.
Він відповідає за створення запитів на звіти, оновлення їх статусів
та, можливо, ініціацію їх генерації.
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.reports.report import ReportModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.reports.report import ReportCreateSchema, ReportUpdateSchema, ReportSchema
from backend.app.src.schemas.reports.request import ReportGenerationRequestSchema # Схема запиту від користувача
from backend.app.src.repositories.reports.report import ReportRepository, report_repository
from backend.app.src.repositories.groups.group import group_repository
from backend.app.src.repositories.dictionaries.status import status_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
from backend.app.src.core.dicts import ReportCodeEnum, ReportStatusEnum # Для валідації report_code та статусів

# TODO: Визначити константи для статусів звітів: # Це TODO вже не актуальне, є Enum
# REPORT_STATUS_QUEUED = "report_queued"
# REPORT_STATUS_PROCESSING = "report_processing"
# REPORT_STATUS_COMPLETED = "report_completed"
# REPORT_STATUS_FAILED = "report_failed"


class ReportService(BaseService[ReportRepository]):
    """
    Сервіс для управління записами про звіти.
    """

    async def get_report_by_id(self, db: AsyncSession, report_id: uuid.UUID, current_user: UserModel) -> ReportModel:
        report = await self.repository.get(db, id=report_id) # Репозиторій може завантажувати зв'язки
        if not report:
            raise NotFoundException(f"Запис звіту з ID {report_id} не знайдено.")

        # Перевірка прав доступу до звіту
        # Супер-адмін бачить все. Адмін групи бачить звіти своєї групи. Користувач - лише свої.
        can_view = False
        if current_user.user_type_code == USER_TYPE_SUPERADMIN:
            can_view = True
        elif report.requested_by_user_id == current_user.id:
            can_view = True
        elif report.group_id:
            from backend.app.src.services.groups.group_membership_service import group_membership_service
            if await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=report.group_id):
                can_view = True

        if not can_view:
            raise ForbiddenException("Ви не маєте доступу до цього звіту.")
        return report

    async def request_report_generation(
        self, db: AsyncSession, *, request_in: ReportGenerationRequestSchema, current_user: UserModel
    ) -> ReportModel:
        """
        Створює запит на генерацію звіту та ставить його в чергу.
        """
        # Валідація report_code (вже відбувається в схемі через Enum)
        report_code_enum = request_in.report_code # Це вже ReportCodeEnum

        # Перевірка існування групи, якщо звіт для групи
        group_id_for_report: Optional[uuid.UUID] = None
        if request_in.parameters and "group_id" in request_in.parameters:
            group_id_for_report = uuid.UUID(str(request_in.parameters["group_id"])) # Переконуємося, що UUID
            group = await group_repository.get(db, id=group_id_for_report)
            if not group:
                raise BadRequestException(f"Група з ID {group_id_for_report} для звіту не знайдена.")

            # Перевірка прав на замовлення звіту для цієї групи
            from backend.app.src.services.groups.group_membership_service import group_membership_service
            if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id_for_report) and \
               current_user.user_type_code != USER_TYPE_SUPERADMIN:
                # Або якщо звичайний користувач може замовляти звіти для своєї групи (залежить від логіки)
                # if not await group_membership_service.is_user_member_of_group(db, user_id=current_user.id, group_id=group_id_for_report):
                raise ForbiddenException(f"Ви не маєте прав замовляти звіти для групи {group_id_for_report}.")

        # TODO: Додаткова валідація `request_in.parameters` на основі `report_code_enum`
        #       (наприклад, чи всі обов'язкові параметри для цього звіту передані).

        queued_status = await status_repository.get_by_code(db, code=ReportStatusEnum.QUEUED.value)
        if not queued_status:
            raise BadRequestException(f"Статус '{ReportStatusEnum.QUEUED.value}' для звітів не знайдено.")

        # Схема ReportCreateSchema очікує report_code, requested_by_user_id, group_id, parameters, status_id
        create_schema = ReportCreateSchema(
            report_code=report_code_enum.value,
            parameters=request_in.parameters,
            # requested_by_user_id, group_id, status_id встановлюються в кастомному методі репозиторію
        )

        return await self.repository.create_report_request(
            db,
            obj_in=create_schema,
            requested_by_id=current_user.id,
            group_id_context=group_id_for_report, # Може бути None для глобальних звітів
            initial_status_id=queued_status.id
        )

    async def update_report_status(
        self, db: AsyncSession, *,
        report_id: uuid.UUID,
        new_status: ReportStatusEnum, # Використовуємо Enum
        file_id: Optional[uuid.UUID] = None,
        error_message: Optional[str] = None # Для статусу FAILED
        # current_user: UserModel # Якщо оновлення статусу ініціюється користувачем (наприклад, скасування)
        # Зазвичай статус оновлюється системним процесом (воркером)
    ) -> ReportModel:
        """
        Оновлює статус генерації звіту та, можливо, посилання на згенерований файл.
        """
        db_report = await self.repository.get(db, id=report_id) # Отримуємо без деталей
        if not db_report:
            raise NotFoundException(f"Запис звіту з ID {report_id} не знайдено.")

        status_model_obj = await status_repository.get_by_code(db, code=new_status.value)
        if not status_model_obj:
            raise BadRequestException(f"Статус '{new_status.value}' для звітів не знайдено в довіднику статусів.")

        update_data: Dict[str, Any] = {"status_id": status_model_obj.id}
        if new_status == ReportStatusEnum.COMPLETED:
            update_data["generated_at"] = datetime.utcnow()
            if file_id:
                # TODO: Перевірити існування файлу з file_id у FileRepository
                update_data["file_id"] = file_id
            else:
                # Якщо звіт COMPLETED, але немає file_id, це може бути помилкою або звіт не файловий.
                # Якщо звіт завжди має бути файлом при COMPLETED, тут можна кинути BadRequestException.
                self.logger.warning(f"Звіт {report_id} позначено як COMPLETED, але не надано file_id.")
        elif new_status == ReportStatusEnum.FAILED:
            # Можна додати поле error_message до ReportModel та ReportUpdateSchema
            if error_message:
                # update_data["error_message"] = error_message # Якщо є таке поле в моделі
                self.logger.error(f"Звіт {report_id} зазнав невдачі: {error_message}")
            else:
                self.logger.error(f"Звіт {report_id} зазнав невдачі без детального повідомлення.")
            pass

        # ReportUpdateSchema може не мати всіх цих полів, тому формуємо словник
        return await self.repository.update(db, db_obj=db_report, obj_in=update_data)

    # TODO: Додати методи для отримання списків звітів з пагінацією та фільтрами
    #       (для користувача, для групи, всі для адміна).
    #       Репозиторій вже має `get_reports_by_user` та `get_reports_for_group`.

report_service = ReportService(report_repository)

# TODO: Реалізувати константи для статусів звітів (REPORT_STATUS_*) в `constants.py`
#       та відповідний Enum в `dicts.py`. (Частково зроблено в коді сервісу).
# TODO: Реалізувати логіку валідації параметрів звіту в `request_report_generation`.
# TODO: Інтеграція з Celery або іншим механізмом фонових задач для асинхронної генерації звітів.
#       Цей сервіс буде створювати запит, а воркер - брати його в обробку,
#       оновлюючи статус та додаючи файл через `update_report_status`.
# TODO: Перевірка прав доступу в `get_report_by_id` та інших методах, що повертають дані.
#
# Все виглядає як хороший початок для ReportService.
# Основна логіка - створення запиту на звіт та оновлення його статусу.
# Генерація самого звіту - це окрема, потенційно складна задача.
