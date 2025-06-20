# backend/app/src/models/dictionaries/statuses.py
# -*- coding: utf-8 -*-
"""Модель SQLAlchemy для довідника "Статуси".

Цей модуль визначає модель `Status`, яка представляє записи в довіднику
загальних статусів системи. Ці статуси можуть використовуватися для різних
сутностей в системі, таких як завдання, користувачі, групи тощо, для
відображення їх поточного стану (наприклад, "активний", "новий", "завершено",
"архівний").

Модель успадковує `BaseDictionary`, що надає їй стандартний набір полів,
включаючи `id`, `name` (для людиночитаної назви статусу), `description` (для опису),
`code` (унікальний текстовий код статусу), а також часові мітки,
можливість м'якого видалення та інші поля з `BaseMainModel`.
"""
# Видалено рядок: from backend.app.src.models.dictionaries.statuses import Status

# Імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionary
# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class Status(BaseDictionary):
    """Модель SQLAlchemy для довідника "Статуси".

    Представляє загальні статуси, які можуть бути застосовані до різних
    сутностей системи.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних: `statuses`.
        __table_args__ (dict): Додаткові параметри таблиці, включаючи коментар.

    Успадковані атрибути з `BaseDictionary` (і, відповідно, з `BaseMainModel`):
        id (Mapped[uuid.UUID]): Унікальний ідентифікатор (UUID).
        name (Mapped[str]): Людиночитана назва статусу (наприклад, "Активний", "В обробці").
        description (Mapped[Optional[str]]): Детальний опис статусу.
        code (Mapped[str]): Унікальний текстовий код статусу (наприклад, "ACTIVE", "IN_PROGRESS").
        icon (Mapped[Optional[str]]): Іконка для візуального представлення.
        color (Mapped[Optional[str]]): Колір для візуального представлення.
        state_id (Mapped[Optional[int]]): Статус самого запису довідника (наприклад, активний/неактивний запис довідника).
        group_id (Mapped[Optional[int]]): Група, до якої може належати запис довідника (якщо застосовно).
        notes (Mapped[Optional[str]]): Додаткові нотатки.
        created_at (Mapped[datetime]): Час створення.
        updated_at (Mapped[datetime]): Час останнього оновлення.
        deleted_at (Mapped[Optional[datetime]]): Час м'якого видалення.
        is_deleted (Mapped[bool]): Прапорець м'якого видалення.
    """
    __tablename__ = "statuses"

    __table_args__ = ({'comment': 'Довідник загальних статусів системи.'},)

    # Для цієї моделі не визначено власних полів, оскільки всі необхідні поля
    # успадковуються від BaseDictionary.
    # Якщо для статусів знадобляться специфічні додаткові атрибути
    # (наприклад, `is_final_status: Mapped[bool]`), їх слід додати тут.

    # _repr_fields визначаються в BaseDictionary та його батьківських класах.
    # Якщо потрібно додати специфічні для Status поля до __repr__,
    # можна визначити тут _repr_fields = ("моє_додаткове_поле",)
    # Поточна реалізація __repr__ в Base збере всі _repr_fields з ієрархії.
    _repr_fields: tuple[str, ...] = () # Немає додаткових полів для __repr__ на цьому рівні


if __name__ == "__main__":
    # Демонстраційний блок для моделі Status.
    logger.info("--- Модель Довідника: Status ---")
    logger.info("Назва таблиці: %s", Status.__tablename__)
    logger.info("Коментар до таблиці: %s", getattr(Status, '__table_args__', ({},))[0].get('comment', ''))


    logger.info("\nОчікувані поля (успадковані та власні):")
    # Поля з BaseMainModel та його міксинів + BaseDictionary
    expected_fields = [
        'id', 'name', 'description', 'code', 'icon', 'color',
        'created_at', 'updated_at', 'deleted_at', 'is_deleted',
        'state_id', 'group_id', 'notes'
    ]
    for field in expected_fields:
        logger.info("  - %s", field)

    # Приклад створення екземпляра (без взаємодії з БД)
    # У реальному коді це робиться через сесію SQLAlchemy.
    # Для демонстрації потрібно імпортувати datetime. uuid більше не використовується для id.
    from datetime import datetime, timezone

    example_status = Status(
        id=1,  # id тепер Integer
        name="Активний", # TODO i18n: "Активний"
        description="Статус для активних елементів системи.", # TODO i18n: "Статус для активних елементів системи."
        code="ACTIVE",
        icon="fas fa-check-circle",
        color="#4CAF50",
        state_id=1, # Припускаючи, що є довідник станів для самих записів довідників
        created_at=datetime.now(timezone.utc) # Імітація встановлення часу
    )

    logger.info("\nПриклад екземпляра Status (без сесії):\n  %s", example_status)
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Status(id=..., name='Активний', code='ACTIVE', icon='fas fa-check-circle', color='#4CAF50', state_id=1, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
