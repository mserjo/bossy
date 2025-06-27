# backend/app/src/services/groups/group_template_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `GroupTemplateService` для управління шаблонами груп.
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.template import GroupTemplateModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав
from backend.app.src.schemas.groups.template import GroupTemplateCreateSchema, GroupTemplateUpdateSchema, GroupTemplateSchema
from backend.app.src.repositories.groups.template import GroupTemplateRepository, group_template_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN

class GroupTemplateService(BaseService[GroupTemplateRepository]):
    """
    Сервіс для управління шаблонами груп.
    Лише супер-адміністратори можуть створювати/редагувати/видаляти шаблони.
    """

    async def get_template_by_id(self, db: AsyncSession, template_id: uuid.UUID) -> GroupTemplateModel:
        template = await self.repository.get(db, id=template_id)
        if not template:
            raise NotFoundException(f"Шаблон групи з ID {template_id} не знайдено.")
        return template

    async def get_template_by_name_and_version(
        self, db: AsyncSession, name: str, version: Optional[int] = None
    ) -> Optional[GroupTemplateModel]:
        """Отримує шаблон за назвою та, опціонально, версією."""
        # `name` тут - це `name` з моделі, яке має бути унікальним для шаблону (разом з версією)
        return await self.repository.get_by_name_and_version(db, name=name, version=version)


    async def get_all_templates(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, only_active: bool = True
    ) -> List[GroupTemplateModel]:
        """Отримує список всіх шаблонів груп (опціонально лише активних)."""
        # `get_all_active_templates` в репозиторії вже фільтрує по is_deleted=False.
        # Якщо потрібна фільтрація за state_id, її треба додати.
        if only_active:
            return await self.repository.get_all_active_templates(db, skip=skip, limit=limit)
        else:
            return await self.repository.get_multi(db, skip=skip, limit=limit, order_by=["name", "version"])


    async def create_template(
        self, db: AsyncSession, *, obj_in: GroupTemplateCreateSchema, current_user: UserModel
    ) -> GroupTemplateModel:
        """Створює новий шаблон групи. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може створювати шаблони груп.")

        # Перевірка на унікальність (name, version) - має бути на рівні БД через UniqueConstraint.
        # Модель GroupTemplateModel вже має UniqueConstraint('name', 'version').
        # Репозиторій BaseRepository.create кине помилку IntegrityError, якщо порушено.

        # `created_by_user_id` має бути встановлено.
        # `GroupTemplateCreateSchema` не має цього поля.
        # Модель `GroupTemplateModel` має `created_by_user_id`.
        create_data = obj_in.model_dump(exclude_unset=True)
        # `group_id` для шаблонів завжди NULL.

        # Якщо `BaseRepository.create` приймає `obj_in: CreateSchemaType`,
        # то потрібно або додати `created_by_user_id` в схему, або створити модель напряму.
        # Створюємо модель напряму, щоб встановити `created_by_user_id`.
        db_template = self.repository.model(created_by_user_id=current_user.id, **create_data)
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        return db_template

    async def update_template(
        self, db: AsyncSession, *, template_id: uuid.UUID, obj_in: GroupTemplateUpdateSchema, current_user: UserModel
    ) -> GroupTemplateModel:
        """Оновлює існуючий шаблон групи. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може оновлювати шаблони груп.")

        db_template = await self.get_template_by_id(db, template_id=template_id) # Перевірка існування

        # Перевірка на унікальність (name, version), якщо вони змінюються
        update_data = obj_in.model_dump(exclude_unset=True)
        if "name" in update_data or "version" in update_data:
            new_name = update_data.get("name", db_template.name)
            new_version = update_data.get("version", db_template.version)
            if new_name != db_template.name or new_version != db_template.version:
                existing = await self.repository.get_by_name_and_version(db, name=new_name, version=new_version)
                if existing and existing.id != template_id:
                    raise BadRequestException(f"Шаблон групи з назвою '{new_name}' та версією {new_version} вже існує.")

        # `updated_by_user_id` має бути встановлено.
        # update_data["updated_by_user_id"] = current_user.id # Якщо модель це підтримує.
        # BaseMainModel має updated_by_user_id, але BaseRepository.update не заповнює його.
        # Це має оброблятися автоматично (event listener) або тут.
        # Поки що покладаємося на автоматичне оновлення `updated_at`.

        return await self.repository.update(db, db_obj=db_template, obj_in=obj_in)

    async def delete_template(
        self, db: AsyncSession, *, template_id: uuid.UUID, current_user: UserModel
    ) -> GroupTemplateModel:
        """Видаляє шаблон групи (м'яке видалення). Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може видаляти шаблони груп.")

        db_template = await self.get_template_by_id(db, template_id=template_id)

        # Використовуємо soft_delete з BaseRepository (якщо реалізовано для BaseMainModel)
        deleted_template = await self.repository.soft_delete(db, db_obj=db_template) # type: ignore
        if not deleted_template:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для шаблонів груп.")
        return deleted_template

group_template_service = GroupTemplateService(group_template_repository)

# TODO: Узгодити встановлення `created_by_user_id` та `updated_by_user_id`.
#       `BaseMainModel` (від якого успадковує `GroupTemplateModel`) має ці поля.
#       `BaseRepository` їх автоматично не заповнює.
#       У `create_template` я додав `created_by_user_id=current_user.id` при створенні моделі.
#       Для `update_template` це ще не оброблено.
#
# TODO: Перевірити, чи `GroupTemplateModel` має `UniqueConstraint('name', 'version')`.
#       (Так, було додано раніше).
#
# Все виглядає як хороший початок для сервісу шаблонів груп.
# Основна логіка - CRUD операції з перевіркою прав супер-адміністратора.
