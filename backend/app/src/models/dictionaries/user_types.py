# backend/app/src/models/dictionaries/user_types.py
# -*- coding: utf-8 -*-
"""Модель SQLAlchemy для довідника "Типи користувачів".

Цей модуль визначає модель `UserTypeModel`, яка представляє записи в довіднику
системних типів користувачів. Ці типи можуть використовуватися для класифікації
користувачів та надання їм різних наборів можливостей або обмежень на рівні системи
(наприклад, "звичайний користувач", "адміністратор платформи", "бот").

Модель успадковує `BaseDictionaryModel`, що надає їй стандартний набір полів,
включаючи `id`, `name` (для людиночитаної назви типу), `description` (для опису),
`code` (унікальний текстовий код типу), а також часові мітки та інші поля.
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
# Імпорт централізованого логера
from backend.app.src.config import logger

# Можливі додаткові імпорти, якщо будуть специфічні поля:
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Boolean, String


class UserType(BaseDictionaryModel):
    """Модель SQLAlchemy для довідника "Типи користувачів".

    Представляє системні типи користувачів (наприклад, "REGULAR_USER", "ADMIN_USER", "BOT_USER").
    Ці типи відрізняються від системних ролей (`UserRole`), які можуть надавати
    більш гранулярні дозволи. Тип користувача може визначати загальну категорію
    або набір базових можливостей.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних: `user_types`.
        __table_args__ (dict): Додаткові параметри таблиці, включаючи коментар.

    Успадковані атрибути з `BaseDictionaryModel`:
        id (Mapped[uuid.UUID]): Унікальний ідентифікатор.
        name (Mapped[str]): Людиночитана назва типу користувача.
        description (Mapped[Optional[str]]): Опис типу користувача.
        code (Mapped[str]): Унікальний текстовий код типу (наприклад, "REGULAR", "BOT").
        icon (Mapped[Optional[str]]): Іконка.
        color (Mapped[Optional[str]]): Колір.
        та інші поля з `BaseMainModel`.
    """
    __tablename__ = "user_types"

    __table_args__ = ({'comment': 'Довідник системних типів користувачів.'},)

    # Якщо для типів користувачів потрібні специфічні додаткові поля,
    # наприклад, чи дозволено цьому типу користувача мати певні привілеї за замовчуванням,
    # або обмеження на кількість створюваних об'єктів, їх можна визначити тут.
    # Наприклад:
    # max_allowed_projects: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Максимальна кількість проектів, яку може створити користувач цього типу."
    # )

    # _repr_fields визначаються в BaseDictionaryModel та його батьківських класах.
    # На цьому рівні немає додаткових полів для __repr__.
    _repr_fields: tuple[str, ...] = ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserType.
    logger.info("--- Модель Довідника: UserType ---")
    logger.info("Назва таблиці: %s", UserType.__tablename__)
    logger.info("Коментар до таблиці: %s", getattr(UserType, '__table_args__', ({},))[0].get('comment', ''))

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'code', 'icon', 'color',
        'created_at', 'updated_at', 'deleted_at', 'is_deleted',
        'state_id', 'group_id', 'notes'
        # 'max_allowed_projects' # Якщо було б додано
    ]
    for field in expected_fields:
        logger.info("  - %s", field)

    # Приклад створення екземпляра (без взаємодії з БД)
    import uuid
    from datetime import datetime, timezone

    example_user_type = UserType(
        id=uuid.uuid4(),
        name="Звичайний користувач", # TODO i18n: "Звичайний користувач"
        description="Стандартний тип користувача з базовим набором прав та можливостей в системі.", # TODO i18n
        code="REGULAR_USER",  # Може відповідати значенням з core.dicts.UserType Enum
        state_id=1 # Приклад ID активного стану з довідника статусів
        # max_allowed_projects=5 # Якщо б поле було додано
    )
    example_user_type.created_at = datetime.now(timezone.utc) # Імітація

    logger.info("\nПриклад екземпляра UserType (без сесії):\n  %s", example_user_type)
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserType(id=..., name='Звичайний користувач', code='REGULAR_USER', state_id=1, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
