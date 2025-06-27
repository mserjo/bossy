# backend/app/src/services/groups/group_settings_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `GroupSettingsService` для управління налаштуваннями груп.
"""

from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.settings import GroupSettingsModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав
from backend.app.src.schemas.groups.settings import GroupSettingsCreateSchema, GroupSettingsUpdateSchema, GroupSettingsSchema
from backend.app.src.repositories.groups.settings import GroupSettingsRepository, group_settings_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки чи адмін групи

class GroupSettingsService(BaseService[GroupSettingsRepository]):
    """
    Сервіс для управління налаштуваннями груп.
    """

    async def get_settings_for_group(self, db: AsyncSession, *, group_id: uuid.UUID) -> GroupSettingsModel:
        """
        Отримує налаштування для вказаної групи.
        Якщо налаштувань немає, може створювати їх за замовчуванням (або кидати помилку).
        """
        settings = await self.repository.get_by_group_id(db, group_id=group_id)
        if not settings:
            # Якщо налаштування обов'язкові для кожної групи, то їх відсутність - помилка.
            # Або ж, тут можна створити їх за замовчуванням.
            # self.logger.info(f"Налаштування для групи {group_id} не знайдено, створюємо за замовчуванням.")
            # default_settings_schema = GroupSettingsCreateSchema() # Використовує дефолти Pydantic
            # settings = await self.repository.create_for_group(db, group_id=group_id, obj_in=default_settings_schema)
            # Поки що кидаємо помилку, створення - відповідальність GroupService.create_group.
            raise NotFoundException(detail=f"Налаштування для групи {group_id} не знайдено.")
        return settings

    async def create_settings_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID, obj_in: GroupSettingsCreateSchema
    ) -> GroupSettingsModel:
        """
        Створює налаштування для групи. Зазвичай викликається при створенні групи.
        Перевіряє, чи налаштування для цієї групи вже не існують.
        """
        existing_settings = await self.repository.get_by_group_id(db, group_id=group_id)
        if existing_settings:
            raise ForbiddenException(detail=f"Налаштування для групи {group_id} вже існують.")

        # GroupSettingsCreateSchema не містить group_id, він передається окремо.
        return await self.repository.create_for_group(db, group_id=group_id, obj_in=obj_in)

    async def update_settings_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID, obj_in: GroupSettingsUpdateSchema, current_user: UserModel
    ) -> GroupSettingsModel:
        """
        Оновлює налаштування для вказаної групи.
        Потребує перевірки прав користувача (чи є він адміном групи).
        """
        db_settings = await self.get_settings_for_group(db, group_id=group_id) # Перевіряє існування

        # TODO: Перевірка прав: current_user має бути адміном групи group_id.
        # from .group_membership_service import group_membership_service # Уникати циклічних імпортів на рівні модуля
        # if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id):
        #     raise ForbiddenException("Ви не маєте прав змінювати налаштування цієї групи.")

        # Перевірка існування bonus_type_id, якщо він оновлюється
        if obj_in.bonus_type_id:
            from backend.app.src.services.dictionaries.bonus_type_service import bonus_type_service as bts
            try:
                await bts.get_by_id(db, id=obj_in.bonus_type_id)
            except NotFoundException:
                raise BadRequestException(f"Тип бонусу з ID {obj_in.bonus_type_id} не знайдено.")

        return await self.repository.update(db, db_obj=db_settings, obj_in=obj_in)

    # Видалення налаштувань зазвичай відбувається разом з видаленням групи (через ondelete="CASCADE").
    # Окремий метод для видалення налаштувань може не знадобитися, або використовується
    # успадкований `delete` з `BaseRepository` (який приймає ID налаштувань, а не group_id).
    # Метод `delete_by_group_id` є в репозиторії.

group_settings_service = GroupSettingsService(group_settings_repository)

# TODO: Реалізувати перевірку прав доступу в `update_settings_for_group`.
#       Це потребуватиме доступу до `GroupMembershipService`.
#       Можна передавати `group_membership_service` як залежність в конструктор,
#       або викликати його статично (якщо екземпляр сервісу глобальний).
#       Або ж, перевірка прав може бути винесена в FastAPI залежність (dependency).
#
# TODO: Узгодити логіку створення налаштувань за замовчуванням.
#       Якщо `get_settings_for_group` не знаходить налаштувань, чи має він їх створювати,
#       чи це завжди робиться при створенні групи?
#       Поточна реалізація `GroupService.create_group` вже створює дефолтні налаштування.
#       Тому `get_settings_for_group` може кидати `NotFoundException`.
#
# Все виглядає як хороший початок для сервісу налаштувань групи.
# `create_settings_for_group` та `update_settings_for_group` - ключові методи.
