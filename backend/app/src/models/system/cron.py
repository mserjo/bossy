# backend/app/src/models/system/cron.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `CronModel` (або `CronTaskModel`)
для зберігання інформації про системні задачі, що виконуються за розкладом (cron jobs).
Ці задачі можуть бути періодичними або разовими та виконуються під спеціальним системним
користувачем (наприклад, "shadow"). Супер-адміністратор може керувати цими задачами.
"""

from sqlalchemy import Column, String, Text, DateTime, Interval, JSON, Boolean, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import uuid # Для роботи з UUID

# TODO: Вирішити, чи успадковувати від BaseMainModel чи BaseModel.
# Якщо задачі мають назву, опис, статус, то BaseMainModel підходить.
# Статус ("активна", "неактивна", "в процесі", "помилка") тут важливий.
# group_id тут не потрібен, бо це системні задачі.
from backend.app.src.models.base import BaseMainModel # Використовуємо BaseMainModel, оскільки задача має назву, опис, статус.

class CronTaskModel(BaseMainModel):
    """
    Модель для системних задач, що виконуються за розкладом (cron).

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор cron-задачі (успадковано).
        name (str): Назва cron-задачі (наприклад, "Щоденне очищення логів") (успадковано).
        description (str | None): Детальний опис задачі (успадковано).
        state_id (uuid.UUID | None): Статус задачі (наприклад, "активна", "неактивна", "виконується", "помилка").
                                     Посилається на довідник статусів. (успадковано)
        group_id (uuid.UUID | None): Для системних cron-задач це поле буде NULL. (успадковано)

        task_identifier (str): Унікальний ідентифікатор задачі в системі планувальника (наприклад, Celery task name).
                               Це може бути шлях до функції, яка виконується.
        cron_expression (str | None): Вираз cron для періодичних задач (наприклад, "0 0 * * *").
                                      Якщо NULL, задача може бути разовою або запускатися за іншою логікою.
        run_once_at (datetime | None): Дата та час для разового запуску задачі.
        interval_value (Interval | None): Інтервал для задач, що повторюються (наприклад, кожні 5 хвилин).
                                          Може використовуватися замість cron_expression.
        task_parameters (JSON | None): Параметри, що передаються у задачу під час виконання (у форматі JSON).
        last_run_at (datetime | None): Час останнього успішного запуску задачі.
        next_run_at (datetime | None): Розрахунковий час наступного запуску задачі.
        is_active (bool): Прапорець, чи активна задача для виконання (додатково до state_id).
        timeout_seconds (int | None): Максимальний час виконання задачі в секундах.
        last_run_status (str | None): Статус останнього виконання ('success', 'failure', 'running').
        last_run_log (Text | None): Лог або повідомлення про помилку останнього виконання.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).
    """
    __tablename__ = "cron_tasks"

    # Ідентифікатор задачі, який використовується системою виконання (наприклад, назва функції Celery)
    # Має бути унікальним, щоб уникнути конфліктів.
    task_identifier: Column[str] = Column(String(255), nullable=False, unique=True, index=True)

    # Cron-вираз для періодичних задач. Наприклад, "0 5 * * 1-5" - о 5 ранку з понеділка по п'ятницю.
    cron_expression: Column[str | None] = Column(String(100), nullable=True)

    # Для разових задач: дата та час, коли задача має бути виконана.
    run_once_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    # Для задач, що повторюються з певним інтервалом (альтернатива cron_expression).
    # Наприклад, datetime.timedelta(minutes=5). SQLAlchemy підтримує тип Interval.
    interval_schedule: Column[Interval | None] = Column(Interval, nullable=True) # SQLAlchemy тип Interval

    # Параметри, які передаються в задачу під час її виконання. Зберігаються у форматі JSON.
    task_parameters: Column[JSON | None] = Column(JSON, nullable=True)

    # Час останнього запуску задачі. Може бути None, якщо задача ще не запускалася.
    last_run_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    # Розрахунковий час наступного запуску задачі.
    # Це поле може оновлюватися планувальником.
    next_run_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True, index=True)

    # Додатковий прапорець для швидкого ввімкнення/вимкнення задачі,
    # не змінюючи її основний `state_id` (який може бути "помилка", "завершено" тощо).
    # `state_id` може вказувати на загальний стан (напр. "Активна для планування", "Вимкнена адміністратором")
    # `is_enabled` може бути тимчасовим перемикачем.
    # TODO: Узгодити використання is_active та state_id. Можливо, достатньо state_id.
    # У BaseMainModel є is_deleted, але тут може знадобитися саме is_active/is_enabled.
    # Якщо state_id використовується для "активна/неактивна", то це поле може бути зайвим.
    # Поки залишаю, але з коментарем. Замінюю на is_enabled для ясності.
    is_enabled: Column[bool] = Column(Boolean, default=True, nullable=False, index=True)

    # Максимальний час виконання задачі в секундах. Якщо перевищено, задача може бути перервана.
    timeout_seconds: Column[int | None] = Column(Integer, nullable=True)

    # Статус останнього виконання: 'success', 'failure', 'running', 'timeout'.
    last_run_status: Column[str | None] = Column(String(50), nullable=True)

    # Детальний лог останнього виконання або повідомлення про помилку.
    last_run_log: Column[str | None] = Column(Text, nullable=True)

    # Поле group_id з BaseMainModel тут нерелевантне, оскільки це системні задачі.
    # Воно буде NULL. Це нормально, оскільки в BaseMainModel group_id є nullable.
    # `state_id` буде посилатися на StatusModel (наприклад, "активна", "неактивна", "помилка виконання").

    # TODO: Зв'язок зі StatusModel для поля state_id (успадковано з BaseMainModel).
    # state = relationship("StatusModel", foreign_keys=[state_id])

    # TODO: Подумати про зв'язок з користувачем, який створив/модифікував задачу (якщо це не завжди superadmin).
    # created_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # updated_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # BaseModel вже має created_by/updated_by, якщо розкоментувати їх.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі CronTaskModel.
        Наприклад: <CronTaskModel(name='Щоденне очищення логів', task_identifier='app.tasks.cleanup_logs')>
        """
        return f"<{self.__class__.__name__}(name='{self.name}', task_identifier='{self.task_identifier}')>"

# Приклади системних задач (згідно technical-task.md):
# - розсилка повідомлень (email, sms, месенджери)
# - очищення логування (старіші за вказану кількість днів)
# - відрізання і пакування логування (старіші за вказану кількість днів)
# - (адмін групи) створення завдання "Привітати з днем народження" - це, скоріше, не системний cron,
#   а налаштування групи, яке генерує завдання або події. Системний cron може перевіряти такі налаштування
#   та створювати відповідні екземпляри завдань.

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# Назва таблиці `cron_tasks` виглядає логічною.
# Поля `task_identifier`, `cron_expression`, `task_parameters`, `last_run_at`, `next_run_at`
# є типовими для таких моделей.
# `state_id` з `BaseMainModel` буде використовуватися для статусу самої cron-задачі (активна, неактивна).
# `is_enabled` додано для гнучкості.
# `last_run_status` та `last_run_log` для моніторингу виконання.
# `run_once_at` та `interval_schedule` для альтернативних способів планування.
# `timeout_seconds` для контролю тривалості виконання.
# Поле `group_id` з `BaseMainModel` буде `None`.
# Поля `name` та `description` з `BaseMainModel` використовуються для опису задачі.
