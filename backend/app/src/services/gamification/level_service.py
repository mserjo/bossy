# backend/app/src/services/gamification/level_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `LevelService` для управління налаштуваннями рівнів гейміфікації.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.gamification.level import LevelModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав
from backend.app.src.schemas.gamification.level import LevelCreateSchema, LevelUpdateSchema, LevelSchema
from backend.app.src.repositories.gamification.level import LevelRepository, level_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE
# from backend.app.src.services.groups.group_membership_service import group_membership_service

class LevelService(BaseService[LevelRepository]):
    """
    Сервіс для управління налаштуваннями рівнів гейміфікації.
    """

    async def get_level_by_id(self, db: AsyncSession, level_id: uuid.UUID) -> LevelModel:
        level = await self.repository.get(db, id=level_id) # Репозиторій може завантажувати зв'язки
        if not level:
            raise NotFoundException(f"Налаштування рівня з ID {level_id} не знайдено.")
        return level

    async def create_level(
        self, db: AsyncSession, *, obj_in: LevelCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> LevelModel:
        """
        Створює нове налаштування рівня в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати налаштування рівнів.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка унікальності level_number та name в межах групи
        existing_level_num = await self.repository.get_by_level_number(db, group_id=group_id, level_number=obj_in.level_number)
        if existing_level_num:
            raise BadRequestException(f"Рівень з номером {obj_in.level_number} вже існує в цій групі.")

        # `name` успадковано з BaseMainModel, для якого UniqueConstraint(group_id, name) вже є в моделі LevelModel
        # existing_level_name = await self.repository.get_by_name_and_group(db, name=obj_in.name, group_id=group_id) # Потрібен такий метод в репо
        # Поки що покладаємося на UniqueConstraint в БД.

        # Встановлення початкового статусу (якщо є)
        if obj_in.state_id:
            status = await status_repository.get(db, id=obj_in.state_id)
            if not status:
                raise BadRequestException(f"Статус з ID {obj_in.state_id} не знайдено.")
        else:
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if not active_status:
                 raise BadRequestException(f"Дефолтний активний статус '{STATUS_ACTIVE_CODE}' не знайдено.")
            # obj_in.state_id = active_status.id # Не можна змінювати obj_in
            # Передаємо в кастомний метод репозиторію або встановлюємо в моделі
            pass # state_id буде встановлено в create_level_for_group

        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id and 'active_status' in locals() and active_status:
             create_data['state_id'] = active_status.id

        # created_by_user_id / updated_by_user_id встановлюються автоматично або сервісом/репозиторієм
        # Тут ми явно передаємо creator_id в репозиторій

        return await self.repository.create_level_for_group(db, obj_in_data=create_data, group_id=group_id, creator_id=current_user.id)

    async def update_level(
        self, db: AsyncSession, *, level_id: uuid.UUID, obj_in: LevelUpdateSchema, current_user: UserModel
    ) -> LevelModel:
        """Оновлює існуюче налаштування рівня."""
        db_level = await self.get_level_by_id(db, level_id=level_id)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_level.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати це налаштування рівня.")

        update_data = obj_in.model_dump(exclude_unset=True)
        # Перевірка унікальності level_number та name, якщо вони змінюються
        if "level_number" in update_data and update_data["level_number"] != db_level.level_number:
            existing_level_num = await self.repository.get_by_level_number(db, group_id=db_level.group_id, level_number=update_data["level_number"])
            if existing_level_num and existing_level_num.id != level_id:
                raise BadRequestException(f"Рівень з номером {update_data['level_number']} вже існує в цій групі.")

        if "name" in update_data and update_data["name"] != db_level.name:
            # Потрібен get_by_name_and_group в репозиторії
            # existing_level_name = await self.repository.get_by_name_and_group(db, name=update_data["name"], group_id=db_level.group_id)
            # if existing_level_name and existing_level_name.id != level_id:
            #     raise BadRequestException(f"Рівень з назвою '{update_data['name']}' вже існує в цій групі.")
            pass # Покладаємося на UniqueConstraint в БД

        return await self.repository.update(db, db_obj=db_level, obj_in=update_data) # obj_in тут словник

    async def delete_level(self, db: AsyncSession, *, level_id: uuid.UUID, current_user: UserModel) -> LevelModel:
        """Видаляє налаштування рівня (м'яке видалення)."""
        db_level = await self.get_level_by_id(db, level_id=level_id)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_level.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти це налаштування рівня.")

        # TODO: Перевірити, чи цей рівень не використовується (чи не досягнутий кимось).
        # Якщо так, видалення може бути заборонене або мати наслідки.
        # user_levels_count = await user_level_repository.count_users_on_level(db, level_id=level_id)
        # if user_levels_count > 0:
        #     raise BadRequestException("Неможливо видалити рівень, оскільки він вже досягнутий користувачами.")

        deleted_level = await self.repository.soft_delete(db, db_obj=db_level) # type: ignore
        if not deleted_level:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для налаштувань рівнів.")
        return deleted_level

level_service = LevelService(level_repository)

# TODO: Реалізувати перевірку `get_by_name_and_group` в `LevelRepository`, якщо потрібно.
# TODO: Реалізувати перевірку використання рівня перед видаленням.
# TODO: Узгодити встановлення `created_by_user_id` / `updated_by_user_id`.
#       (Метод `create_level_for_group` в репозиторії не встановлює `created_by_user_id`).
#       Це має робити сервіс або `BaseRepository.create` має бути адаптований.
#       Я змінив `create_level_for_group` в репозиторії, щоб він приймав `obj_in_data`,
#       а сервіс тут готує цей словник, включаючи `created_by_user_id`.
#       Але `LevelCreateSchema` не має `created_by_user_id`.
#       Тому `create_level_for_group` в репозиторії має приймати `creator_id` окремо.
#       Виправляю `LevelRepository.create_level_for_group`.
#       Ні, `LevelModel` успадковує `BaseMainModel`, який має `created_by_user_id`.
#       Сервіс має передавати його в `obj_in_data` для `self.model(**obj_in_data)`.
#       Я додав `created_by_user_id=current_user.id` в `create_level_for_group` репозиторію.
#       (Це було зроблено в `TaskRepository.create_task_in_group`, аналогічно тут).
#       Оновлення: `LevelRepository.create_level_for_group` вже приймає `obj_in_data`
#       і встановлює `group_id`. `created_by_user_id` має бути в `obj_in_data`,
#       якщо це поле є в `LevelCreateSchema` або додається сервісом.
#       `LevelCreateSchema` не має `created_by_user_id`.
#       Тому `db_obj = self.model(group_id=group_id, created_by_user_id=current_user.id, **obj_in_data)`
#       в репозиторії `create_level_for_group` - це правильний підхід.
#       (Перевірив, `LevelRepository.create_level_for_group` вже це робить).
#
# Все виглядає як хороший початок для LevelService.
