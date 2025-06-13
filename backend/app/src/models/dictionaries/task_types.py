# backend/app/src/models/dictionaries/task_types.py
# -*- coding: utf-8 -*-
"""Модель SQLAlchemy для довідника "Типи завдань".

Цей модуль визначає модель `TaskTypeModel`, яка представляє записи в довіднику
типів завдань. Ці типи використовуються для класифікації завдань в системі,
наприклад: "Звичайне завдання", "Складне завдання", "Подія", "Штраф".
Типи завдань можуть впливати на логіку їх обробки, нарахування балів,
доступність для певних груп користувачів тощо.

Модель успадковує `BaseDictionaryModel`, що надає їй стандартний набір полів
(id, name, description, code, часові мітки, тощо).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Можливі додаткові імпорти SQLAlchemy, якщо будуть специфічні поля:
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Boolean, Integer


class TaskType(BaseDictionaryModel):
    """Модель SQLAlchemy для довідника "Типи завдань".

    Представляє різні типи завдань, що можуть існувати в системі
    (наприклад, "REGULAR_TASK", "COMPLEX_TASK", "EVENT", "FINE").

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних: `task_types`.
        __table_args__ (dict): Додаткові параметри таблиці, включаючи коментар.

    Успадковані атрибути з `BaseDictionaryModel`:
        id (Mapped[uuid.UUID]): Унікальний ідентифікатор.
        name (Mapped[str]): Людиночитана назва типу завдання.
        description (Mapped[Optional[str]]): Опис типу завдання.
        code (Mapped[str]): Унікальний текстовий код типу завдання.
        icon (Mapped[Optional[str]]): Іконка.
        color (Mapped[Optional[str]]): Колір.
        та інші поля з `BaseMainModel`.
    """
    __tablename__ = "task_types"

    __table_args__ = ({'comment': 'Довідник типів завдань (наприклад, звичайне, складне, подія, штраф).'},)

    # Якщо для типів завдань потрібні специфічні додаткові поля, їх можна визначити тут.
    # Наприклад:
    # default_points: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Кількість балів за замовчуванням для цього типу завдання."
    # )
    # is_penalty: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="Чи є цей тип завдання штрафом (призводить до списання балів)."
    # )

    # _repr_fields визначаються в BaseDictionaryModel та його батьківських класах.
    # На цьому рівні немає додаткових полів для __repr__.
    _repr_fields: tuple[str, ...] = ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі TaskType.
    logger.info("--- Модель Довідника: TaskType ---")
    logger.info("Назва таблиці: %s", TaskType.__tablename__)
    logger.info("Коментар до таблиці: %s", getattr(TaskType, '__table_args__', ({},))[0].get('comment', ''))

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'code', 'icon', 'color',
        'created_at', 'updated_at', 'deleted_at', 'is_deleted',
        'state_id', 'group_id', 'notes'
        # 'default_points', 'is_penalty' # Якщо були б додані
    ]
    for field in expected_fields:
        logger.info("  - %s", field)

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_task_type = TaskType(
        id=1, # id тепер Integer
        name="Звичайне завдання", # TODO i18n: "Звичайне завдання"
        description="Стандартний тип завдання з базовими параметрами та нарахуванням балів.", # TODO i18n
        code="REGULAR_TASK",  # Може відповідати значенням з core.dicts.TaskType Enum
        state_id=1 # Приклад ID активного стану
        # default_points=10, # Якщо б поле було додано
        # is_penalty=False   # Якщо б поле було додано
    )
    example_task_type.created_at = datetime.now(timezone.utc) # Імітація

    logger.info("\nПриклад екземпляра TaskType (без сесії):\n  %s", example_task_type)
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <TaskType(id=..., name='Звичайне завдання', code='REGULAR_TASK', state_id=1, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
