# backend/app/src/workers/base_task.py
# -*- coding: utf-8 -*-
"""
Базовий клас для завдань Celery.

Цей модуль може визначати кастомний базовий клас Task для Celery,
що дозволяє додати спільну логіку, обробку помилок, налаштування сесії БД
або інші функції для всіх завдань Celery в проекті.
"""

from celery import Task
# from backend.app.src.config.database import SessionLocal, engine # Для сесії БД
# from backend.app.src.config.logging import get_logger

# logger = get_logger(__name__)

# Приклад кастомного базового класу Task
# class DatabaseTask(Task):
#     """
#     Базове завдання Celery з автоматичним управлінням сесією бази даних.
#     """
#     _db = None # Кешована сесія БД для екземпляра завдання
#
#     def after_return(self, status, retval, task_id, args, kwargs, einfo):
#         """
#         Обробник, що викликається після завершення завдання.
#         Закриває сесію БД, якщо вона була відкрита.
#         """
#         if self._db is not None:
#             logger.debug(f"Task {self.name}[{task_id}] closing DB session.")
#             self._db.close()
#             self._db = None
#         super().after_return(status, retval, task_id, args, kwargs, einfo)
#
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         """
#         Обробник, що викликається при помилці у виконанні завдання.
#         Виконує rollback та закриває сесію БД.
#         """
#         logger.error(f"Task {self.name}[{task_id}] failed: {exc}", exc_info=einfo)
#         if self._db is not None:
#             logger.debug(f"Task {self.name}[{task_id}] rolling back and closing DB session due to failure.")
#             self._db.rollback() # Спробувати відкотити, якщо сесія активна
#             self._db.close()
#             self._db = None
#         super().on_failure(exc, task_id, args, kwargs, einfo)
#
#     @property
#     def db(self):
#         """
#         Надає екземпляр сесії SQLAlchemy.
#         Створює нову сесію, якщо вона ще не існує для цього екземпляра завдання.
#         """
#         if self._db is None:
#             logger.debug(f"Task {self.name} creating new DB session.")
#             # Важливо: SessionLocal() створює нову сесію.
#             # Для Celery воркерів, які можуть бути багатопотоковими або багатопроцесними,
#             # потрібно переконатися, що кожне завдання або потік/процес воркера
#             # використовує власну сесію БД.
#             # Використання `scoped_session` може бути альтернативою, якщо налаштовано правильно.
#             self._db = SessionLocal()
#         return self._db

# Щоб використовувати цей базовий клас, завдання Celery мають бути декоровані так:
# from backend.app.src.workers.celery_app import celery_app
# from backend.app.src.workers.base_task import DatabaseTask
#
# @celery_app.task(base=DatabaseTask, name="my_db_task")
# def my_database_task(arg1, arg2):
#     # Доступ до сесії БД через self.db
#     # result = self.db.query(...).all()
#     # self.db.commit() # Якщо були зміни
#     # ...
#     pass

# На даний момент, якщо не потрібен кастомний базовий клас, цей файл може
# залишатися порожнім або містити лише цей коментар-пояснення.
# Стандартний celery.Task буде використовуватися за замовчуванням.

logger_stub = lambda: None # Заглушка для логера, поки він не налаштований
logger_stub.info = print
logger_stub.debug = print
logger_stub.error = print
logger_stub.warning = print

class BaseTask(Task):
    """
    Простий базовий клас для завдань Celery, щоб продемонструвати можливість.
    Можна додати логування початку/кінця завдання тощо.
    """
    def on_start(self, task_id, args, kwargs):
        logger_stub.info(f"ЗАВДАННЯ РОЗПОЧАТО: {self.name}[{task_id}] з args={args} kwargs={kwargs}")

    def on_success(self, retval, task_id, args, kwargs):
        logger_stub.info(f"ЗАВДАННЯ УСПІШНЕ: {self.name}[{task_id}], результат: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger_stub.error(f"ЗАВДАННЯ ПРОВАЛЕНЕ: {self.name}[{task_id}], помилка: {exc}", exc_info=einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger_stub.info(f"ЗАВДАННЯ ЗАВЕРШЕНО: {self.name}[{task_id}], статус: {status}")

# Для використання: @celery_app.task(base=BaseTask)

__all__ = [
    "BaseTask",
    # "DatabaseTask", # Якщо реалізовано
]
