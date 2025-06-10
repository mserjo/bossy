# backend/app/src/models/dictionaries/task_types.py
"""
Модель SQLAlchemy для довідника "Типи завдань".

Цей модуль визначає модель `TaskType`, яка представляє записи в довіднику
типів завдань (наприклад, "Звичайне завдання", "Складне завдання", "Подія", "Штраф"
відповідно до `core.dicts.TaskType` або технічного завдання).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Boolean

class TaskType(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Типи завдань".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для системних типів завдань, ймовірно, буде NULL.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_task_types`).
    """
    __tablename__ = "dict_task_types"

    # Якщо для типів завдань потрібні специфічні додаткові поля,
    # наприклад, чи дозволяє цей тип завдання множинне виконання,
    # їх можна визначити тут.
    # Наприклад:
    # allows_multiple_completions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Чи дозволено множинне виконання")

    # _repr_fields успадковуються та збираються автоматично.
    # Додавання специфічних полів до __repr__:
    # _repr_fields = ["allows_multiple_completions"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі TaskType.
    logger.info("--- Модель Довідника: TaskType ---")
    logger.info(f"Назва таблиці: {TaskType.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.append('allows_multiple_completions')
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_task_type = TaskType(
        id=1,
        name="Звичайне завдання",
        description="Стандартний тип завдання з базовими параметрами.",
        code="REGULAR_TASK",  # Може відповідати значенням з core.dicts.TaskType
        state="active"
    )

    logger.info(f"\nПриклад екземпляра TaskType (без сесії):\n  {example_task_type}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <TaskType(id=1, name='Звичайне завдання', code='REGULAR_TASK', state='active')>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
