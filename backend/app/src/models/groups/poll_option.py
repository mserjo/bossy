# backend/app/src/models/groups/poll_option.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `PollOptionModel` для зберігання варіантів відповідей
для опитувань (`PollModel`). Кожне опитування може мати декілька варіантів відповідей.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseModel, оскільки варіант відповіді - це проста сутність,
# що належить опитуванню. `name` чи `description` з `BaseMainModel` тут можуть бути надлишковими,
# оскільки текст варіанту - це основне поле.
# Однак, якщо варіанти можуть мати опис або власний статус, BaseMainModel може бути кращим.
# Поки що зупинимося на варіанті з текстом відповіді як основним полем.
# Якщо використовувати BaseMainModel, то `name` буде текстом варіанту.
# Спробуємо з BaseMainModel, де `name` - це текст варіанту.
# `group_id` та `state_id` з `BaseMainModel` тут не дуже релевантні.
# Краще створити простішу базу або успадкувати від BaseModel і додати потрібні поля.
# Зупинимось на BaseModel і додамо поле `text`.
from backend.app.src.models.base import BaseModel

class PollOptionModel(BaseModel):
    """
    Модель для зберігання варіантів відповідей для опитування.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор варіанту відповіді (успадковано).
        poll_id (uuid.UUID): Ідентифікатор опитування, до якого належить цей варіант.
        option_text (Text): Текст варіанту відповіді.
        order_num (int): Порядковий номер варіанту для сортування та відображення.
        # votes_count (int): Лічильник голосів за цей варіант (може бути денормалізованим або обчислюваним).

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).

    Зв'язки:
        poll (relationship): Зв'язок з PollModel.
        votes (relationship): Список голосів, поданих за цей варіант (PollVoteModel).
    """
    __tablename__ = "poll_options"

    poll_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)

    # Текст варіанту відповіді.
    option_text: Column[str] = Column(Text, nullable=False)

    # Порядковий номер для сортування варіантів відповідей.
    order_num: Column[int] = Column(Integer, default=0, nullable=False)

    # Лічильник голосів. Може бути корисним для швидкого відображення результатів,
    # але потребує синхронізації при додаванні/видаленні голосів.
    # Або ж можна обчислювати динамічно через `len(poll_option.votes)`.
    # Поки що не додаємо, щоб уникнути денормалізації.
    # votes_count: Column[int] = Column(Integer, default=0, nullable=False)


    # --- Зв'язки (Relationships) ---
    poll = relationship("PollModel", back_populates="options")

    # Голоси, подані за цей конкретний варіант відповіді
    votes = relationship("PollVoteModel", back_populates="option", cascade="all, delete-orphan")


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі PollOptionModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', poll_id='{self.poll_id}', text='{self.option_text[:50]}...')>"

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `structure-claude-v3.md` вказує `poll_option.py`.
# Назва таблиці `poll_options` є логічною.
# Ключові поля: `poll_id`, `option_text`, `order_num`.
# `ondelete="CASCADE"` для `poll_id` означає, що при видаленні опитування
# його варіанти відповідей також будуть видалені.
# Зв'язки з `PollModel` та `PollVoteModel` визначені.
# Використання `BaseModel` як основи.
# Поле `order_num` важливе для збереження порядку варіантів, заданого користувачем.
# Все виглядає узгоджено.
# Роздуми про `votes_count`: вирішено не додавати для уникнення проблем з синхронізацією денормалізованих даних.
# Кількість голосів можна буде отримати через `len(option.votes)`.
# Якщо продуктивність стане проблемою, можна буде додати це поле пізніше.
