# backend/app/src/services/groups/poll_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `PollService` для управління опитуваннями/голосуваннями в групах.
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.poll import PollModel, PollOptionModel, PollVoteModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.groups.poll import (
    PollCreateSchema, PollUpdateSchema, PollSchema,
    PollOptionCreateSchema, PollOptionUpdateSchema, PollOptionSchema,
    PollVoteCreateSchema, PollVoteSchema
)
from backend.app.src.repositories.groups.poll import PollRepository, poll_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки існування групи
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки прав

class PollService(BaseService[PollRepository]):
    """
    Сервіс для управління опитуваннями, їх варіантами відповідей та голосами.
    """

    async def get_poll_by_id(self, db: AsyncSession, poll_id: uuid.UUID, include_details: bool = True) -> PollModel:
        poll = None
        if include_details:
            poll = await self.repository.get_poll_with_options_and_votes(db, poll_id=poll_id)
        else:
            poll = await self.repository.get(db, id=poll_id)
        if not poll:
            raise NotFoundException(f"Опитування з ID {poll_id} не знайдено.")
        return poll

    async def create_poll_in_group(
        self, db: AsyncSession, *, obj_in: PollCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> PollModel:
        """
        Створює нове опитування в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати опитування.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено для створення опитування.")

        # Створення PollModel
        poll_data_dict = obj_in.model_dump(exclude={"options"}, exclude_unset=True) # Виключаємо опції, вони створюються окремо

        # Встановлюємо group_id та created_by_user_id
        # `PollCreateSchema` не має цих полів, вони встановлюються тут.
        new_poll = self.repository.model(
            group_id=group_id,
            created_by_user_id=current_user.id,
            **poll_data_dict
        )
        db.add(new_poll)
        await db.flush() # Потрібен ID для опцій

        # Створення PollOptionModel
        if obj_in.options:
            for option_in in obj_in.options:
                db_option = PollOptionModel(poll_id=new_poll.id, **option_in.model_dump())
                db.add(db_option)

        await db.commit()
        await db.refresh(new_poll)
        # Для завантаження опцій після створення
        await db.refresh(new_poll, attribute_names=['options'])
        return new_poll

    async def update_poll(
        self, db: AsyncSession, *, poll_id: uuid.UUID, obj_in: PollUpdateSchema, current_user: UserModel
    ) -> PollModel:
        """Оновлює існуюче опитування."""
        db_poll = await self.get_poll_by_id(db, poll_id=poll_id, include_details=False) # Не потрібні деталі для оновлення самого опитування

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_poll.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати це опитування.")

        # TODO: Логіка оновлення варіантів відповідей (PollOptionModel), якщо вони передані в obj_in.
        # Це може бути складним: видалення старих, оновлення існуючих, додавання нових.
        # Поки що `PollUpdateSchema` не містить поля `options`.
        # Якщо потрібно оновлювати опції, краще мати окремі ендпоінти/методи сервісу для опцій.

        # Оновлюємо сам PollModel
        # `updated_by_user_id` має оновлюватися (якщо є в моделі)
        update_data = obj_in.model_dump(exclude_unset=True)
        # update_data["updated_by_user_id"] = current_user.id # Якщо потрібно

        updated_poll = await self.repository.update(db, db_obj=db_poll, obj_in=update_data)
        await db.refresh(updated_poll, attribute_names=['options', 'creator', 'state', 'group']) # Оновлюємо зв'язки
        return updated_poll

    async def delete_poll(self, db: AsyncSession, *, poll_id: uuid.UUID, current_user: UserModel) -> PollModel:
        """Видаляє опитування."""
        db_poll = await self.get_poll_by_id(db, poll_id=poll_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_poll.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти це опитування.")

        # Використовуємо "тверде" видалення. `ondelete="CASCADE"` в моделях має видалити опції та голоси.
        deleted_poll = await self.repository.delete(db, id=poll_id)
        if not deleted_poll: # Малоймовірно, якщо get_poll_by_id не кинув виняток
            raise NotFoundException(f"Опитування з ID {poll_id} не знайдено для видалення.")
        return deleted_poll # Повертає видалений об'єкт

    # --- Методи для Poll Options ---
    async def add_poll_option(self, db: AsyncSession, *, poll_id: uuid.UUID, option_in: PollOptionCreateSchema, current_user: UserModel) -> PollOptionModel:
        poll = await self.get_poll_by_id(db, poll_id, include_details=False) # Перевірка існування та прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=poll.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав додавати варіанти до цього опитування.")
        return await self.repository.add_option_to_poll(db, poll_id=poll.id, option_in=option_in)

    async def update_poll_option(self, db: AsyncSession, *, option_id: uuid.UUID, option_in: PollOptionUpdateSchema, current_user: UserModel) -> PollOptionModel:
        db_option = await self.repository.get_poll_option(db, option_id)
        if not db_option:
            raise NotFoundException(f"Варіант відповіді з ID {option_id} не знайдено.")
        poll = await self.get_poll_by_id(db, db_option.poll_id, include_details=False) # Для перевірки прав на опитування
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=poll.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати варіанти цього опитування.")
        return await self.repository.update_poll_option(db, db_option=db_option, option_in=option_in)

    # --- Методи для Poll Votes ---
    async def cast_vote(
        self, db: AsyncSession, *, poll_id: uuid.UUID, option_ids: List[uuid.UUID], current_user: UserModel
    ) -> List[PollVoteModel]:
        """Дозволяє користувачеві проголосувати."""
        poll = await self.get_poll_by_id(db, poll_id, include_details=True) # Потрібні деталі (is_anonymous, allow_multiple_choices, options)

        # Перевірка, чи є користувач членом групи
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        membership = await group_membership_service.get_membership_by_user_and_group(db, user_id=current_user.id, group_id=poll.group_id)
        if not membership: # Або якщо членство неактивне
            raise ForbiddenException("Лише члени групи можуть голосувати в цьому опитуванні.")

        # Перевірка, чи опитування активне (не завершене)
        if poll.ends_at and poll.ends_at < datetime.utcnow():
            raise BadRequestException("Голосування завершено.")
        # TODO: Перевірка state_id опитування, якщо використовується для активності.

        # Перевірка кількості обраних варіантів
        if not poll.allow_multiple_choices and len(option_ids) > 1:
            raise BadRequestException("Це опитування не дозволяє обирати декілька варіантів.")
        if len(option_ids) < poll.min_choices:
            raise BadRequestException(f"Мінімальна кількість обраних варіантів: {poll.min_choices}.")
        if poll.max_choices is not None and len(option_ids) > poll.max_choices:
            raise BadRequestException(f"Максимальна кількість обраних варіантів: {poll.max_choices}.")

        # Перевірка, чи всі обрані option_id належать цьому poll_id
        valid_option_ids = {opt.id for opt in poll.options}
        for opt_id in option_ids:
            if opt_id not in valid_option_ids:
                raise BadRequestException(f"Варіант відповіді з ID {opt_id} не належить цьому опитуванню.")

        # Перевірка, чи користувач вже не голосував (якщо не дозволено повторне голосування або зміна голосу)
        # І якщо опитування не анонімне.
        # Поточна логіка не передбачає зміну голосу, лише додавання.
        # UniqueConstraint в PollVoteModel ('poll_id', 'user_id', 'option_id') запобігає дублюванню голосу за той самий варіант.
        # Якщо allow_multiple_choices=False, то сервіс має перевірити, чи немає вже голосів від цього user_id для цього poll_id.
        if not poll.allow_multiple_choices and not poll.is_anonymous:
            existing_votes = await self.repository.get_user_votes_for_poll(db, user_id=current_user.id, poll_id=poll.id)
            if existing_votes:
                raise BadRequestException("Ви вже проголосували в цьому опитуванні.")

        created_votes = []
        user_id_for_vote = None if poll.is_anonymous else current_user.id
        for option_id in option_ids:
            # Додаткова перевірка, чи не голосував вже за цей варіант (якщо allow_multiple_choices=True)
            if not poll.is_anonymous:
                existing_vote_for_option = await self.repository.get_user_vote_for_option(db, user_id=current_user.id, poll_id=poll.id, option_id=option_id)
                if existing_vote_for_option:
                    # Пропустити цей варіант або кинути помилку, якщо не можна голосувати за той самий варіант двічі
                    self.logger.info(f"Користувач {current_user.id} вже голосував за варіант {option_id} в опитуванні {poll.id}.")
                    continue

            vote = await self.repository.add_vote(db, poll_id=poll.id, option_id=option_id, user_id=user_id_for_vote)
            created_votes.append(vote)

        if not created_votes and option_ids: # Якщо були обрані варіанти, але жодного голосу не створено (наприклад, всі дублікати)
             raise BadRequestException("Не вдалося зарахувати голоси (можливо, ви вже голосували за ці варіанти).")

        return created_votes

    async def get_poll_results(self, db: AsyncSession, poll_id: uuid.UUID, current_user: Optional[UserModel] = None) -> Dict[uuid.UUID, int]:
        """Отримує результати голосування (кількість голосів за кожен варіант)."""
        poll = await self.get_poll_by_id(db, poll_id, include_details=False) # Не потрібні голоси, лише сам poll

        # Перевірка видимості результатів
        can_view_results = False
        if poll.results_visibility == "always":
            can_view_results = True
        elif poll.results_visibility == "after_voting" and not poll.is_anonymous:
            # Перевірити, чи поточний користувач голосував
            if current_user:
                user_votes = await self.repository.get_user_votes_for_poll(db, user_id=current_user.id, poll_id=poll.id)
                if user_votes:
                    can_view_results = True
        elif poll.results_visibility == "after_end":
            if poll.ends_at and poll.ends_at <= datetime.utcnow():
                can_view_results = True

        # Адміни групи та суперадміни завжди бачать результати
        if current_user:
            from backend.app.src.services.groups.group_membership_service import group_membership_service
            if current_user.user_type_code == USER_TYPE_SUPERADMIN or \
               await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=poll.group_id):
                can_view_results = True

        if not can_view_results:
            # Можна повернути порожній словник або кинути ForbiddenException,
            # залежно від того, як API має реагувати.
            # Поки що повертаємо порожній словник, щоб не ламати клієнт, який очікує результати.
            # Або краще кидати помилку, щоб клієнт знав, що результати недоступні.
            raise ForbiddenException("Результати цього опитування наразі недоступні для вас.")

        return await self.repository.get_vote_counts_for_poll(db, poll_id=poll.id)


poll_service = PollService(poll_repository)

# TODO: Додати перевірку прав для всіх методів, що змінюють дані (update_poll, add_poll_option тощо).
# TODO: Реалізувати TODO в `get_polls_for_group` щодо фільтрації за активним статусом.
# TODO: Реалізувати TODO в `cast_vote` щодо перевірки, чи не голосував вже користувач,
#       якщо `allow_multiple_choices=False` і опитування не анонімне.
#       (Частково зроблено, але потребує уваги).
# TODO: Узгодити логіку `results_visibility` в `get_poll_results`.
#
# Все виглядає як хороший початок для сервісу опитувань.
# Включає логіку для створення опитувань з варіантами, голосування, отримання результатів.
# Використовує PollRepository, який містить методи для PollOption та PollVote.
# Потребує імпорту `group_membership_service` для перевірки прав.
# Важливо обережно обробляти циклічні імпорти, якщо вони виникнуть.
