# backend/app/src/repositories/groups/poll.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `PollModel` та пов'язаних з нею
моделей `PollOptionModel` та `PollVoteModel`.
Надає методи для управління опитуваннями/голосуваннями в групах.
"""

from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import select, func, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload, joinedload # type: ignore

from backend.app.src.models.groups.poll import PollModel
from backend.app.src.models.groups.poll_option import PollOptionModel
from backend.app.src.models.groups.poll_vote import PollVoteModel
from backend.app.src.schemas.groups.poll import (
    PollCreateSchema, PollUpdateSchema,
    PollOptionCreateSchema, PollOptionUpdateSchema,
    PollVoteCreateSchema
)
from backend.app.src.repositories.base import BaseRepository

# --- Репозиторій для PollModel ---
class PollRepository(BaseRepository[PollModel, PollCreateSchema, PollUpdateSchema]):
    """
    Репозиторій для роботи з моделлю опитувань/голосувань (`PollModel`).
    """

    async def get_poll_with_options_and_votes(self, db: AsyncSession, poll_id: uuid.UUID) -> Optional[PollModel]:
        """
        Отримує опитування разом з його варіантами відповідей та голосами.
        """
        statement = select(self.model).where(self.model.id == poll_id).options(
            selectinload(self.model.options).selectinload(PollOptionModel.votes), # Завантажуємо опції, а для кожної опції - голоси
            selectinload(self.model.creator) # Інформація про творця опитування
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_polls_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
        include_options: bool = False, # Чи включати варіанти відповідей
        only_active: bool = False # Чи повертати лише активні/незавершені опитування
    ) -> List[PollModel]:
        """
        Отримує список опитувань для вказаної групи.
        """
        statement = select(self.model).where(self.model.group_id == group_id)

        if only_active:
            # TODO: Додати умову для активних опитувань (наприклад, state_id або ends_at > now)
            # statement = statement.where(self.model.state.has(code="active")) # Приклад
            statement = statement.where(
                (self.model.ends_at > datetime.utcnow()) | (self.model.ends_at == None) # type: ignore
            )
            # Також можна перевіряти state_id, якщо він використовується для "активності" опитування

        if include_options:
            statement = statement.options(selectinload(self.model.options))

        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # CRUD для PollOptionModel та PollVoteModel можуть бути реалізовані тут
    # або в окремих репозиторіях, якщо логіка складна.
    # Поки що додамо базові операції для них сюди для простоти.

    async def add_option_to_poll(
        self, db: AsyncSession, *, poll_id: uuid.UUID, option_in: PollOptionCreateSchema
    ) -> PollOptionModel:
        """Додає варіант відповіді до опитування."""
        db_option = PollOptionModel(poll_id=poll_id, **option_in.model_dump())
        db.add(db_option)
        await db.commit()
        await db.refresh(db_option)
        return db_option

    async def get_poll_option(self, db: AsyncSession, option_id: uuid.UUID) -> Optional[PollOptionModel]:
        """Отримує варіант відповіді за ID."""
        return await db.get(PollOptionModel, option_id)

    async def update_poll_option(
        self, db: AsyncSession, *, db_option: PollOptionModel, option_in: PollOptionUpdateSchema
    ) -> PollOptionModel:
        """Оновлює варіант відповіді."""
        update_data = option_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_option, field, value)
        db.add(db_option)
        await db.commit()
        await db.refresh(db_option)
        return db_option

    async def delete_poll_option(self, db: AsyncSession, option_id: uuid.UUID) -> Optional[PollOptionModel]:
        """Видаляє варіант відповіді."""
        db_option = await self.get_poll_option(db, option_id)
        if db_option:
            await db.delete(db_option)
            await db.commit()
        return db_option

    async def add_vote(
        self, db: AsyncSession, *, poll_id: uuid.UUID, option_id: uuid.UUID, user_id: Optional[uuid.UUID]
    ) -> PollVoteModel:
        """Додає голос користувача."""
        # Перевірка, чи може користувач голосувати (наприклад, не голосував раніше, якщо не дозволено кілька разів)
        # та чи є опитування активним - це логіка сервісу.
        db_vote = PollVoteModel(poll_id=poll_id, option_id=option_id, user_id=user_id)
        db.add(db_vote)
        await db.commit()
        await db.refresh(db_vote)
        return db_vote

    async def get_user_vote_for_option(
        self, db: AsyncSession, *, user_id: uuid.UUID, poll_id: uuid.UUID, option_id: uuid.UUID
    ) -> Optional[PollVoteModel]:
        """Перевіряє, чи голосував користувач за конкретний варіант в опитуванні."""
        statement = select(PollVoteModel).where(
            PollVoteModel.user_id == user_id,
            PollVoteModel.poll_id == poll_id,
            PollVoteModel.option_id == option_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_votes_for_poll(
        self, db: AsyncSession, *, user_id: uuid.UUID, poll_id: uuid.UUID
    ) -> List[PollVoteModel]:
        """Отримує всі голоси користувача в конкретному опитуванні."""
        statement = select(PollVoteModel).where(
            PollVoteModel.user_id == user_id,
            PollVoteModel.poll_id == poll_id
        )
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_vote_counts_for_poll(self, db: AsyncSession, poll_id: uuid.UUID) -> Dict[uuid.UUID, int]:
        """Отримує кількість голосів для кожного варіанту відповіді в опитуванні."""
        statement = select(PollVoteModel.option_id, func.count(PollVoteModel.id).label("vote_count") # type: ignore
                  ).where(PollVoteModel.poll_id == poll_id
                  ).group_by(PollVoteModel.option_id)

        result = await db.execute(statement)
        return {row.option_id: row.vote_count for row in result.all()}


poll_repository = PollRepository(PollModel)

# TODO: Розглянути можливість винесення логіки для PollOptionModel та PollVoteModel
#       в окремі репозиторії (`PollOptionRepository`, `PollVoteRepository`), якщо
#       кількість методів для них значно зросте. Поки що вони в `PollRepository` для зручності.
# TODO: Додати перевірку `group_id IS NOT NULL` для `PollModel` через `__table_args__` в моделі.
#       (Це вже було зроблено для PollModel).
# TODO: Узгодити `back_populates` для всіх зв'язків з відповідними моделями.
#       - `PollModel.creator` -> `UserModel.created_polls`
#       - `PollModel.options` -> `PollOptionModel.poll`
#       - `PollModel.votes` -> `PollVoteModel.poll`
#       - `PollOptionModel.votes` -> `PollVoteModel.option`
#       - `PollVoteModel.user` -> `UserModel.poll_votes_made`
#
# Все виглядає як хороший набір методів для управління опитуваннями.
# Використання `selectinload` для завантаження пов'язаних даних.
# Метод `get_vote_counts_for_poll` корисний для відображення результатів.
