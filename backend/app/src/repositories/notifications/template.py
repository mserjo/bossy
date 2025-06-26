# backend/app/src/repositories/notifications/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `NotificationTemplateModel`.
Надає методи для управління шаблонами сповіщень.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_, or_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.notifications.template import NotificationTemplateModel
from backend.app.src.schemas.notifications.template import NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class NotificationTemplateRepository(BaseRepository[NotificationTemplateModel, NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema]):
    """
    Репозиторій для роботи з моделлю шаблонів сповіщень (`NotificationTemplateModel`).
    """

    async def get_by_template_code(self, db: AsyncSession, *, template_code: str) -> Optional[NotificationTemplateModel]:
        """
        Отримує шаблон за його унікальним програмним кодом.
        """
        statement = select(self.model).where(self.model.template_code == template_code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def find_template(
        self, db: AsyncSession, *,
        notification_type_code: str,
        channel_code: str,
        language_code: str,
        group_id: Optional[uuid.UUID] = None
    ) -> Optional[NotificationTemplateModel]:
        """
        Знаходить найбільш відповідний шаблон сповіщення.
        Логіка пріоритетів:
        1. Специфічний для групи, мови, типу та каналу.
        2. Глобальний для мови, типу та каналу.
        3. TODO: Можливо, дефолтний англійський глобальний, якщо для потрібної мови немає.
        """
        # 1. Пошук специфічного для групи
        if group_id:
            statement_group = select(self.model).where(
                and_(
                    self.model.notification_type_code == notification_type_code,
                    self.model.channel_code == channel_code,
                    self.model.language_code == language_code,
                    self.model.group_id == group_id,
                    self.model.is_deleted == False # type: ignore # Припускаючи, що BaseMainModel має is_deleted
                    # TODO: Додати перевірку на активний state_id, якщо потрібно
                )
            )
            result_group = await db.execute(statement_group)
            template = result_group.scalar_one_or_none()
            if template:
                return template

        # 2. Пошук глобального для вказаної мови
        statement_global = select(self.model).where(
            and_(
                self.model.notification_type_code == notification_type_code,
                self.model.channel_code == channel_code,
                self.model.language_code == language_code,
                self.model.group_id == None, # type: ignore
                self.model.is_deleted == False # type: ignore
                # TODO: Додати перевірку на активний state_id
            )
        )
        result_global = await db.execute(statement_global)
        template_global = result_global.scalar_one_or_none()
        if template_global:
            return template_global

        # TODO: 3. Пошук дефолтного глобального (наприклад, англійською), якщо вище не знайдено.
        # if language_code != "en": # Приклад дефолтної мови
        #     statement_default_lang = select(self.model).where(...) # аналогічно, але language_code="en"
        #     ...
        #     if template_default_lang: return template_default_lang

        return None # Якщо жоден шаблон не знайдено

    # `create`, `update`, `delete` (включаючи soft_delete) успадковані.
    # `NotificationTemplateCreateSchema` та `NotificationTemplateUpdateSchema` використовуються.
    # `group_id` може бути NULL для глобальних шаблонів.
    # `template_code` має бути унікальним.
    # `name` (з BaseMainModel) - описова назва.

notification_template_repository = NotificationTemplateRepository(NotificationTemplateModel)

# TODO: Узгодити логіку `find_template` з вимогами до дефолтних шаблонів та мов.
#       Поточна реалізація шукає груповий, потім глобальний для вказаної мови.
#       Потрібно додати логіку для fallback на дефолтну мову (наприклад, англійську).
# TODO: Перевірити використання `is_deleted` та `state_id` для визначення "активного" шаблону.
#       `NotificationTemplateModel` успадковує `BaseMainModel`, тому має ці поля.
#
# Все виглядає як хороший початок для репозиторію шаблонів.
# `get_by_template_code` для прямого доступу.
# `find_template` для інтелектуального пошуку.
