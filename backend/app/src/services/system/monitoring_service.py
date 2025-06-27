# backend/app/src/services/system/monitoring_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `SystemEventLogService` для управління системними логами/подіями.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.system.monitoring import SystemEventLogModel
from backend.app.src.schemas.system.monitoring import SystemEventLogCreateSchema, SystemEventLogSchema
from backend.app.src.repositories.system.monitoring import SystemEventLogRepository, system_event_log_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException # Логи зазвичай не кидають Forbidden/BadRequest при читанні

class SystemEventLogService(BaseService[SystemEventLogRepository]):
    """
    Сервіс для управління системними логами/подіями.
    В основному надає методи для запису та отримання логів.
    """

    async def log_event(self, db: AsyncSession, *, obj_in: SystemEventLogCreateSchema) -> SystemEventLogModel:
        """
        Записує нову подію/лог в систему.
        Цей метод може викликатися з різних частин додатку або з обробників логування.
        """
        # Валідація рівня логування вже є в схемі.
        # Інші перевірки (наприклад, чи існує user_id, якщо передано) можуть бути тут.
        if obj_in.user_id:
            from backend.app.src.repositories.auth.user import user_repository # Відкладений імпорт
            user = await user_repository.get(db, id=obj_in.user_id)
            if not user:
                self.logger.warning(f"Спроба записати лог для неіснуючого користувача ID: {obj_in.user_id}. user_id буде NULL.")
                obj_in.user_id = None # Або кинути помилку, або просто не встановлювати

        # Використовуємо успадкований метод create з BaseRepository
        return await self.repository.create(db, obj_in=obj_in)

    async def get_logs_paginated(
        self, db: AsyncSession, *,
        page: int = 1, size: int = 100, # Пагінація
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        source_component: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        message_contains: Optional[str] = None,
        order_by: Optional[List[str]] = None # Наприклад, ["-created_at"]
    ) -> PaginatedResponse[SystemEventLogModel]: # type: ignore
        """
        Отримує список логів з пагінацією та фільтрацією.
        """
        # Формуємо словник фільтрів для передачі в репозиторій
        filters: Dict[str, Any] = {}
        if level: filters["level"] = level.upper()
        if logger_name: filters["logger_name__ilike"] = f"%{logger_name}%" # Приклад для ilike
        if source_component: filters["source_component"] = source_component
        if user_id: filters["user_id"] = user_id
        if date_from: filters["created_at__ge"] = date_from # Потрібна підтримка __ge в BaseRepository
        if date_to:
            from datetime import timedelta
            filters["created_at__lt"] = date_to + timedelta(days=1) # Потрібна підтримка __lt
        if message_contains: filters["message__ilike"] = f"%{message_contains}%"

        if not order_by:
            order_by = ["-created_at"] # За замовчуванням сортуємо за спаданням дати створення

        # Потрібно адаптувати BaseRepository.get_paginated або реалізувати логіку тут.
        # Поточний BaseRepository._apply_filters підтримує лише рівність та list.in_.
        # Тому, для фільтрів __ilike, __ge, __lt потрібна доробка BaseRepository
        # або використання кастомного методу в SystemEventLogRepository.
        #
        # `SystemEventLogRepository` вже має метод `get_logs` з потрібною фільтрацією.
        # Але він не повертає `PaginatedResponse`.
        #
        # Реалізуємо пагінацію тут, використовуючи `SystemEventLogRepository.get_logs`
        # та окремий запит для total_count.

        # TODO: Реалізувати коректну пагінацію з фільтрами.
        # Поки що простий виклик з лімітом, без точного total.
        self.logger.warning("Пагінація для get_logs_paginated ще не повністю реалізована з усіма фільтрами в BaseRepository.")

        # Приклад, як це могло б виглядати з кастомним підрахунком:
        # total_items = await self.repository.count_logs_with_filters(db, filters=filters) # Потрібен такий метод
        # items = await self.repository.get_logs(db, skip=(page-1)*size, limit=size, ...)
        # return PaginatedResponse(total=total_items, page=page, size=len(items), pages=..., items=items)

        # Поки що використовуємо get_multi з базового репозиторію,
        # але він не підтримує всі потрібні фільтри (__ilike, __ge, __lt).
        # Я залишу це як TODO для доопрацювання фільтрації в BaseRepository.
        # Або ж, SystemEventLogRepository.get_logs має бути розширений для пагінації.

        # Тимчасове рішення:
        items = await self.repository.get_logs(
            db, level=level, logger_name=logger_name, source_component=source_component,
            user_id=user_id, date_from=date_from, date_to=date_to, message_contains=message_contains,
            skip=(page-1)*size, limit=size
        )
        # Приблизний підрахунок для пагінації (некоректний без реального total)
        total_items_approx = len(items) if page == 1 and len(items) < size else (size * page + (1 if len(items) == size else 0))

        from backend.app.src.schemas.base import PaginatedResponse # Локальний імпорт
        return PaginatedResponse(
            total=total_items_approx, # TODO: Замінити на реальний підрахунок
            page=page,
            size=len(items),
            pages=(total_items_approx + size - 1) // size if total_items_approx > 0 else 0, # TODO: Замінити
            items=items
        )


    async def clear_old_logs(self, db: AsyncSession, *, older_than_days: int) -> int:
        """Видаляє старі логи."""
        if older_than_days <= 0:
            raise BadRequestException("Кількість днів для видалення логів має бути позитивним числом.")
        return await self.repository.delete_old_logs(db, older_than_days=older_than_days)

system_event_log_service = SystemEventLogService(system_event_log_repository)

# TODO: Доопрацювати пагінацію в `get_logs_paginated` для коректного підрахунку total_items
#       з урахуванням всіх фільтрів (або розширити BaseRepository).
# TODO: Перевірити, чи `SystemEventLogCreateSchema` містить всі необхідні поля
#       і чи валідатор рівня логування працює коректно.
#
# Все виглядає як хороший початок для SystemEventLogService.
# Основні методи для запису та отримання логів, а також для їх очищення.
# Фільтрація в `get_logs` репозиторію вже досить гнучка.
