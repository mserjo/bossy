# backend/app/src/services/notifications/notification_template_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `NotificationTemplateService` для управління шаблонами сповіщень.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.notifications.template import NotificationTemplateModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав (superuser)
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema, NotificationTemplateSchema
)
from backend.app.src.repositories.notifications.template import NotificationTemplateRepository, notification_template_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE
from backend.app.src.core.dicts import NotificationTypeEnum, NotificationChannelEnum # Для валідації

class NotificationTemplateService(BaseService[NotificationTemplateRepository]):
    """
    Сервіс для управління шаблонами сповіщень.
    Зазвичай, лише супер-адміністратори мають повний доступ до управління шаблонами.
    Адміністратори груп можуть мати можливість переглядати або кастомізувати
    обмежений набір шаблонів для своєї групи (якщо така логіка буде реалізована).
    """

    async def get_template_by_id(self, db: AsyncSession, template_id: uuid.UUID) -> NotificationTemplateModel:
        template = await self.repository.get(db, id=template_id)
        if not template:
            raise NotFoundException(f"Шаблон сповіщення з ID {template_id} не знайдено.")
        return template

    async def get_template_by_code(self, db: AsyncSession, template_code: str) -> NotificationTemplateModel:
        template = await self.repository.get_by_template_code(db, template_code=template_code)
        if not template:
            raise NotFoundException(f"Шаблон сповіщення з кодом '{template_code}' не знайдено.")
        return template

    async def find_template_for_notification(
        self, db: AsyncSession, *,
        notification_type_code: Union[str, NotificationTypeEnum],
        channel_code: Union[str, NotificationChannelEnum],
        language_code: str, # Наприклад, "uk", "en"
        group_id: Optional[uuid.UUID] = None
    ) -> Optional[NotificationTemplateModel]:
        """
        Знаходить найбільш відповідний активний шаблон для заданих параметрів.
        Використовує логіку пріоритетів з репозиторію.
        """
        # Переконуємося, що передані коди є рядками (значеннями Enum)
        nt_code_str = notification_type_code.value if isinstance(notification_type_code, NotificationTypeEnum) else notification_type_code
        ch_code_str = channel_code.value if isinstance(channel_code, NotificationChannelEnum) else channel_code

        return await self.repository.find_template(
            db,
            notification_type_code=nt_code_str,
            channel_code=ch_code_str,
            language_code=language_code,
            group_id=group_id
        )

    async def create_template(
        self, db: AsyncSession, *, obj_in: NotificationTemplateCreateSchema, current_user: UserModel
    ) -> NotificationTemplateModel:
        """Створює новий шаблон сповіщення. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може створювати шаблони сповіщень.")

        # Перевірка унікальності template_code (вже є в моделі)
        existing_by_code = await self.repository.get_by_template_code(db, template_code=obj_in.template_code)
        if existing_by_code:
            raise BadRequestException(f"Шаблон з кодом '{obj_in.template_code}' вже існує.")

        # Перевірка унікальності комбінації (type, channel, lang, group_id) - реалізовано в БД
        # Але можна додати перевірку тут, щоб уникнути помилки БД.
        # existing_combo = await self.repository.find_template(...)
        # if existing_combo:
        #     raise BadRequestException("Шаблон з такою комбінацією параметрів вже існує.")


        # Перевірка існування групи, якщо group_id вказано
        if obj_in.group_id:
            group = await group_repository.get(db, id=obj_in.group_id)
            if not group:
                raise BadRequestException(f"Група з ID {obj_in.group_id} не знайдена.")

        # Встановлення статусу, якщо не передано
        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id:
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if active_status:
                create_data['state_id'] = active_status.id
            else:
                self.logger.warning(f"Активний статус '{STATUS_ACTIVE_CODE}' не знайдено, шаблон буде створено без статусу.")

        # `created_by_user_id` для шаблону (якщо модель його має)
        # Модель NotificationTemplateModel успадковує BaseMainModel, тому має created_by_user_id
        # create_data["created_by_user_id"] = current_user.id

        # Використовуємо успадкований create, який приймає схему
        # Потрібно переконатися, що obj_in (NotificationTemplateCreateSchema) містить всі поля,
        # які приймає конструктор моделі, або BaseRepository.create їх обробляє.
        # BaseRepository.create робить self.model(**jsonable_encoder(obj_in)).
        # Тому схема має бути сумісною.
        # `created_by_user_id` має бути додано до `create_data` перед викликом create,
        # якщо воно не встановлюється автоматично.
        # Поля BaseModel (id, created_at, updated_at, created_by_user_id, updated_by_user_id)
        # зазвичай не включаються в CreateSchema.
        # `created_by_user_id` встановлюється тут.

        db_template = self.repository.model(created_by_user_id=current_user.id, **create_data)
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        return db_template


    async def update_template(
        self, db: AsyncSession, *, template_id: uuid.UUID, obj_in: NotificationTemplateUpdateSchema, current_user: UserModel
    ) -> NotificationTemplateModel:
        """Оновлює існуючий шаблон. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може оновлювати шаблони сповіщень.")

        db_template = await self.get_template_by_id(db, template_id=template_id)

        update_data = obj_in.model_dump(exclude_unset=True)
        # Перевірка унікальності `template_code`, якщо він змінюється
        if "template_code" in update_data and update_data["template_code"] != db_template.template_code:
            existing_by_code = await self.repository.get_by_template_code(db, template_code=update_data["template_code"])
            if existing_by_code and existing_by_code.id != template_id:
                raise BadRequestException(f"Шаблон з кодом '{update_data['template_code']}' вже існує.")

        # TODO: Перевірка унікальності комбінації (type, channel, lang, group_id), якщо ключові поля змінюються.

        # `updated_by_user_id`
        # update_data["updated_by_user_id"] = current_user.id

        return await self.repository.update(db, db_obj=db_template, obj_in=update_data) # obj_in тут словник

    async def delete_template(
        self, db: AsyncSession, *, template_id: uuid.UUID, current_user: UserModel
    ) -> NotificationTemplateModel:
        """Видаляє шаблон (м'яке видалення). Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може видаляти шаблони сповіщень.")

        db_template = await self.get_template_by_id(db, template_id=template_id)
        # TODO: Перевірити, чи шаблон не використовується активно (хоча м'яке видалення це дозволяє).

        deleted_template = await self.repository.soft_delete(db, db_obj=db_template) # type: ignore
        if not deleted_template: # Модель успадковує BaseMainModel, тому має підтримувати
            raise BadRequestException(f"Не вдалося видалити шаблон {template_id}.")
        return deleted_template

notification_template_service = NotificationTemplateService(notification_template_repository)

# TODO: Реалізувати TODO в `find_template` (fallback на дефолтну мову).
# TODO: Додати перевірку унікальності комбінації полів при оновленні.
# TODO: Узгодити встановлення `created_by_user_id` / `updated_by_user_id`.
#       (Вирішено: сервіс встановлює `created_by_user_id` при створенні моделі напряму).
#
# Все виглядає як хороший початок для сервісу шаблонів сповіщень.
# Основна логіка - CRUD з перевіркою прав супер-адміністратора та унікальності кодів.
# Метод `find_template` є ключовим для системи сповіщень.
