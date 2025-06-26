# backend/app/src/repositories/files/avatar.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `AvatarModel`.
Надає методи для управління зв'язками між користувачами та їх аватарами.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, update, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.files.avatar import AvatarModel
from backend.app.src.schemas.files.avatar import AvatarCreateSchema, AvatarUpdateSchema # Схеми для створення/оновлення
from backend.app.src.repositories.base import BaseRepository

class AvatarRepository(BaseRepository[AvatarModel, AvatarCreateSchema, AvatarUpdateSchema]):
    """
    Репозиторій для роботи з моделлю аватарів (`AvatarModel`).
    """

    async def get_current_avatar_for_user(self, db: AsyncSession, *, user_id: uuid.UUID) -> Optional[AvatarModel]:
        """
        Отримує поточний (активний) аватар для вказаного користувача.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :return: Об'єкт AvatarModel або None, якщо поточного аватара немає.
        """
        statement = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.is_current == True)
        ).options(selectinload(self.model.file)) # Завантажуємо пов'язаний файл
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_avatar_history_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[AvatarModel]:
        """
        Отримує історію аватарів для вказаного користувача.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :return: Список об'єктів AvatarModel, відсортованих за датою створення (новіші спочатку).
        """
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.file) # Завантажуємо пов'язані файли
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def set_avatar_as_current(
        self, db: AsyncSession, *, user_id: uuid.UUID, avatar_id: uuid.UUID
    ) -> Optional[AvatarModel]:
        """
        Встановлює вказаний аватар як поточний для користувача,
        деактивуючи попередній поточний аватар.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :param avatar_id: Ідентифікатор запису AvatarModel, який потрібно зробити поточним.
        :return: Оновлений об'єкт AvatarModel (новий поточний) або None, якщо аватар не знайдено.
        """
        # 1. Деактивувати всі поточні аватари для цього користувача
        update_statement = (
            update(self.model)
            .where(and_(self.model.user_id == user_id, self.model.is_current == True))
            .values(is_current=False)
        )
        await db.execute(update_statement)

        # 2. Встановити новий аватар як поточний
        new_current_avatar = await self.get(db, avatar_id)
        if new_current_avatar and new_current_avatar.user_id == user_id:
            new_current_avatar.is_current = True
            db.add(new_current_avatar)
            await db.commit()
            await db.refresh(new_current_avatar)
            return new_current_avatar
        else:
            # Якщо новий аватар не знайдено або він не належить користувачеві,
            # відкочуємо зміни (деактивацію попередніх).
            # Або ж, якщо логіка дозволяє, просто не встановлюємо новий.
            # Поки що просто повертаємо None, припускаючи, що сервіс перевірить належність.
            await db.rollback() # Відкочуємо деактивацію, якщо новий не встановлено
            return None


    async def create_avatar_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID, file_id: uuid.UUID
    ) -> AvatarModel:
        """
        Створює новий запис AvatarModel для користувача, встановлюючи його як поточний
        та деактивуючи попередні.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :param file_id: Ідентифікатор файлу (з FileModel), який є аватаром.
        :return: Створений об'єкт AvatarModel.
        """
        # Деактивуємо попередні поточні аватари
        update_statement = (
            update(self.model)
            .where(and_(self.model.user_id == user_id, self.model.is_current == True))
            .values(is_current=False)
        )
        await db.execute(update_statement)

        # Створюємо новий запис аватара
        # `AvatarCreateSchema` може не мати `is_current`, оскільки він завжди True при створенні.
        # Або ж, якщо `AvatarCreateSchema` має `is_current`, то передаємо його.
        # Поточна `AvatarCreateSchema` не має `is_current`.
        create_schema = AvatarCreateSchema(user_id=user_id, file_id=file_id)

        # Використовуємо успадкований метод create, але він очікує схему.
        # Або створюємо модель напряму.
        db_obj = self.model(
            user_id=create_schema.user_id,
            file_id=create_schema.file_id,
            is_current=True # Новий аватар завжди поточний
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований, може використовуватися для зміни `is_current` через `AvatarUpdateSchema`.
    # `delete` успадкований для видалення запису AvatarModel (і, можливо, пов'язаного FileModel через каскад або сервіс).

avatar_repository = AvatarRepository(AvatarModel)

# TODO: Переконатися, що `AvatarCreateSchema` та `AvatarUpdateSchema` відповідають потребам.
#       `AvatarCreateSchema` може бути дуже простою (лише user_id, file_id),
#       оскільки `is_current` завжди True при створенні нового аватара.
#       `AvatarUpdateSchema` може бути лише для зміни `is_current`.
#
# TODO: Розглянути логіку видалення файлів (`FileModel`) при видаленні запису `AvatarModel`,
#       якщо файл аватара більше не використовується. Це відповідальність сервісного шару.
#
# Все виглядає добре. Надано методи для отримання поточного аватара, історії,
# встановлення поточного та створення нового (з деактивацією старих).
