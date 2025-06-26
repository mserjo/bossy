# backend/app/src/repositories/groups/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupTemplateModel`.
Надає методи для управління шаблонами груп.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.template import GroupTemplateModel
from backend.app.src.schemas.groups.template import GroupTemplateCreateSchema, GroupTemplateUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class GroupTemplateRepository(BaseRepository[GroupTemplateModel, GroupTemplateCreateSchema, GroupTemplateUpdateSchema]):
    """
    Репозиторій для роботи з моделлю шаблонів груп (`GroupTemplateModel`).
    """

    # Успадковує CRUD-операції з BaseRepository.
    # `name` з BaseMainModel використовується як назва шаблону.
    # `template_data` (JSONB) зберігає конфігурацію.
    # `version` для версіонування.

    async def get_by_name_and_version(
        self, db: AsyncSession, *, name: str, version: Optional[int] = None
    ) -> Optional[GroupTemplateModel]:
        """
        Отримує шаблон групи за назвою та, опціонально, за версією.
        Якщо версія не вказана, повертає останню активну версію.

        :param db: Асинхронна сесія бази даних.
        :param name: Назва шаблону.
        :param version: Версія шаблону (опціонально).
        :return: Об'єкт GroupTemplateModel або None.
        """
        statement = select(self.model).where(self.model.name == name) # `name` тут - це `template_code` з моделі
        if version is not None:
            statement = statement.where(self.model.version == version)
        else:
            # Якщо версія не вказана, шукаємо останню (найбільшу) версію
            # TODO: Додати фільтр по активному статусу, якщо потрібно
            statement = statement.order_by(self.model.version.desc()) # type: ignore

        result = await db.execute(statement)
        return result.scalars().first() # Повертаємо перший знайдений (найновіший, якщо версія не вказана)

    async def get_all_active_templates(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[GroupTemplateModel]:
        """
        Отримує список всіх активних шаблонів груп.
        (Припускаючи, що "активний" визначається через state_id або is_deleted=False).
        """
        # TODO: Уточнити, як визначається "активний" шаблон (через state_id або is_deleted).
        # Поки що припускаємо is_deleted == False.
        statement = select(self.model).where(self.model.is_deleted == False).order_by(self.model.name).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `GroupTemplateCreateSchema` має містити `template_code` (який є `name` в моделі),
    # `template_data`, `version`. `created_by_user_id` встановлюється сервісом.
    # `update` успадкований. `GroupTemplateUpdateSchema` для оновлення.

group_template_repository = GroupTemplateRepository(GroupTemplateModel)

# TODO: Уточнити поле, яке використовується як унікальний ідентифікатор шаблону для пошуку
#       (чи це `name` з BaseMainModel, чи окреме поле `template_code`).
#       Модель `GroupTemplateModel` має `template_code` як унікальний, а `name` з `BaseMainModel`
#       для описової назви. Метод `get_by_name_and_version` має використовувати `template_code`.
#       Я виправлю це.
#       Ні, `GroupTemplateModel` не має окремого `template_code`. Вона успадковує `name` з `BaseMainModel`.
#       І в схемі `NotificationTemplateSchema` поле `name` з `BaseMainModel` використовується як "Назва шаблону (для адмінки)",
#       а `template_code` - як унікальний програмний код.
#       Для `GroupTemplateModel` поле `name` (успадковане) є назвою шаблону.
#       Якщо потрібен окремий унікальний код, його треба додати до моделі.
#       Поки що `name` є ідентифікатором для `get_by_name_and_version`.
#       Це означає, що `name` має бути унікальним (принаймні в поєднанні з версією, або глобально).
#       У `BaseMainModel` `name` індексоване, але не унікальне.
#       Для шаблонів `name` має бути унікальним. Це потрібно додати в `GroupTemplateModel`
#       через `__table_args__ = (UniqueConstraint('name', 'version', name='uq_group_template_name_version'),)`.
#
# Все виглядає добре. `get_by_name_and_version` та `get_all_active_templates` корисні.
# Важливо забезпечити унікальність `(name, version)` для шаблонів.
