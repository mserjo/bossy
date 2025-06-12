# backend/app/src/services/tasks/scheduler.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.task import Task  # Модель SQLAlchemy Task
from backend.app.src.models.tasks.assignment import TaskAssignment  # Для призначення завдань
from backend.app.src.models.dictionaries.statuses import Status  # Для отримання статусу за замовчуванням
# from backend.app.src.models.auth.user import User # Не використовується прямо тут, але опосередковано через Task.created_by_user
# from backend.app.src.services.tasks.task import TaskService # Для створення нових екземплярів завдань (щоб уникнути циркулярності, поки що пряма інстанціація)
# from backend.app.src.services.tasks.assignment import TaskAssignmentService # Для призначення повторюваних завдань
# from backend.app.src.services.notifications.notification import NotificationService # Для нагадувань (замість InternalNotificationService)

from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Винести типи повторень в Enum або в довідник в БД.
RECURRENCE_DAILY = "DAILY"
RECURRENCE_WEEKLY = "WEEKLY"
RECURRENCE_MONTHLY = "MONTHLY"
RECURRENCE_YEARLY = "YEARLY"
DEFAULT_TASK_STATUS_CODE_OPEN = "OPEN"  # Статус для нових екземплярів завдань


class TaskSchedulingService(BaseService):
    """
    Сервіс для обробки запланованих та повторюваних завдань/подій.
    Включає логіку для створення екземплярів повторюваних завдань,
    надсилання нагадувань про наближення термінів виконання та потенційно
    автоматичне призначення завдань.

    Примітка: Фактичний виклик цих методів зазвичай ініціюється планувальником
    завдань (наприклад, Celery Beat, APScheduler, cron), який викликає ці методи сервісу
    з відповідними інтервалами.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        # Щоб уникнути циркулярних залежностей на рівні модуля, залежні сервіси
        # можуть бути інстанційовані локально в методах або передані при ініціалізації,
        # якщо керуються через DI контейнер. Поки що, деякі виклики сервісів будуть концептуальними заглушками.
        logger.info("TaskSchedulingService ініціалізовано.")

    async def process_recurring_tasks(self) -> List[UUID]:
        """
        Визначає шаблони повторюваних завдань, для яких настав час створення нового екземпляра,
        та створює ці нові екземпляри.
        Цей метод має викликатися періодично (наприклад, щодня).

        :return: Список ID новостворених екземплярів завдань.
        """
        logger.info("Обробка повторюваних завдань...")
        now = datetime.now(timezone.utc)
        newly_created_task_ids: List[UUID] = []

        # Запит передбачає, що модель Task має: is_recurring_template, is_active, recurrence_end_date
        stmt = select(Task).where(
            Task.is_recurring_template == True,
            Task.is_active == True,  # Обробляємо тільки активні шаблони
            (Task.recurrence_end_date.is_(None) | (Task.recurrence_end_date > now))  # type: ignore
        ).options(
            selectinload(Task.group),
            selectinload(Task.task_type),
            selectinload(Task.status),  # Для отримання status_id за замовчуванням для нового екземпляра
            selectinload(Task.created_by_user)  # Для отримання оригінального творця
            # TODO: Завантажити default_assignees, якщо вони зберігаються з шаблоном
        )
        recurring_templates_db = (await self.db_session.execute(stmt)).scalars().all()

        for template in recurring_templates_db:
            if await self._should_create_new_instance(template, now):
                try:
                    logger.info(
                        f"Створення нового екземпляра для шаблону повторюваного завдання ID: {template.id} ('{template.title}')")

                    # TODO: Реалізувати надійний розрахунок наступної дати виконання, враховуючи recurrence_pattern.
                    new_due_date = await self._calculate_next_due_date(template, now)
                    if not new_due_date:  # Якщо не вдалося розрахувати (напр. непідтримуваний патерн)
                        logger.warning(
                            f"Не вдалося розрахувати наступну дату виконання для шаблону ID {template.id}. Пропуск.")
                        continue

                    # Використовуємо статус шаблону, якщо він дійсний, інакше статус "OPEN"
                    status_id_to_set = template.status_id
                    if not status_id_to_set or not await self.db_session.get(Status, status_id_to_set):
                        open_status = (await self.db_session.execute(
                            select(Status).where(Status.code == DEFAULT_TASK_STATUS_CODE_OPEN))
                                       ).scalar_one_or_none()
                        if not open_status:
                            logger.error(
                                f"Статус за замовчуванням '{DEFAULT_TASK_STATUS_CODE_OPEN}' не знайдено, неможливо створити екземпляр для шаблону {template.id}")
                            continue
                        status_id_to_set = open_status.id

                    # TODO: Розглянути використання TaskService.create_task для створення, якщо вдасться уникнути циркулярності.
                    #  Це забезпечить узгодженість логіки створення завдань.
                    new_instance_data = {
                        "title": template.title, "description": template.description,
                        "group_id": template.group_id, "task_type_id": template.task_type_id,
                        "status_id": status_id_to_set, "due_date": new_due_date,
                        "points_reward": template.points_reward,
                        "penalty_points_on_missed": template.penalty_points_on_missed,
                        "is_recurring_template": False,  # Це екземпляр
                        "parent_task_id": template.id,  # Посилання на шаблон завдання
                        "created_by_user_id": template.created_by_user_id,  # Або ID системного користувача
                        "updated_by_user_id": template.created_by_user_id,  # Або ID системного користувача
                        "is_active": True,  # Нові екземпляри активні за замовчуванням
                        "is_mandatory": template.is_mandatory,
                        "execution_type": template.execution_type,
                        # TODO: Скопіювати інші релевантні поля з шаблону, якщо потрібно.
                    }
                    # Видаляємо None значення, щоб не перезаписувати значення за замовчуванням в моделі
                    new_instance_data_cleaned = {k: v for k, v in new_instance_data.items() if v is not None}

                    new_instance_model = Task(**new_instance_data_cleaned)
                    self.db_session.add(new_instance_model)
                    await self.db_session.flush()  # Отримуємо ID для логування та можливих призначень
                    newly_created_task_ids.append(new_instance_model.id)
                    logger.info(
                        f"Створено новий екземпляр завдання ID: {new_instance_model.id} для шаблону ID: {template.id}")

                    template.last_instance_created_at = now  # Оновлюємо час створення останнього екземпляра
                    self.db_session.add(template)

                    # TODO: Якщо шаблон мав призначення за замовчуванням, призначити їх новому екземпляру.
                    # from backend.app.src.services.tasks.assignment import TaskAssignmentService # Локальний імпорт
                    # assignment_service = TaskAssignmentService(self.db_session)
                    # # ... логіка копіювання призначень ...

                except Exception as e:
                    logger.error(f"Помилка обробки шаблону повторюваного завдання ID {template.id}: {e}",
                                 exc_info=global_settings.DEBUG)
                    # Важливо: не робимо тут rollback всієї транзакції, помилка одного шаблону не має зупиняти інші.
                    # Якщо _initialize_dictionary та _initialize_system_users робили flush замість commit,
                    # то тут можна було б зробити rollback для конкретного шаблону, але це складно.
                    # Поточна логіка з commit після кожної категорії в run_full_initialization є компромісом.
                    # Якщо тут виникає помилка, то зміни для цього шаблону не будуть закомічені, якщо commit в кінці.
                    # Якщо sub-методи комітять, то тут rollback не вплине на попередні успішні коміти.
                    # Для обробки повторюваних завдань, краще мати один коміт в кінці.
                    # Поки що, припускаємо, що помилка тут не має валити всю пачку.
                    pass  # Продовжуємо з наступним шаблоном

        if newly_created_task_ids:
            try:
                await self.commit()  # Один коміт для всіх успішно створених екземплярів та оновлень шаблонів
                logger.info(
                    f"Успішно оброблено повторювані завдання. Створено {len(newly_created_task_ids)} нових екземплярів.")
            except Exception as e:
                logger.error(f"Помилка коміту екземплярів повторюваних завдань: {e}", exc_info=global_settings.DEBUG)
                await self.rollback()
                newly_created_task_ids.clear()  # Очищаємо список, оскільки коміт не вдався
        else:
            logger.info("Немає нових екземплярів повторюваних завдань для створення цього разу.")

        return newly_created_task_ids

    async def _should_create_new_instance(self, template_task: Task, current_time: datetime) -> bool:
        """Визначає, чи потрібно створювати новий екземпляр для шаблону повторюваного завдання."""
        # TODO: Реалізувати надійну логіку перевірки на основі `template_task.recurrence_pattern` (наприклад, RRule, cron)
        #  та `template_task.last_instance_created_at`. Використати бібліотеку типу `dateutil.rrule`.

        if not template_task.is_recurring_template: return False  # Це не шаблон

        interval = template_task.recurrence_interval  # Наприклад, "DAILY", "WEEKLY", "MONTHLY"
        last_created_at = template_task.last_instance_created_at
        # recurrence_start_date визначає, коли шаблон починає діяти
        start_date = getattr(template_task, 'recurrence_start_date', template_task.created_at)

        if start_date and current_time < start_date:  # Ще не час починати
            return False

        # recurrence_end_date визначає, коли шаблон перестає діяти
        if template_task.recurrence_end_date and current_time > template_task.recurrence_end_date:
            logger.info(
                f"Шаблон повторюваного завдання ID {template_task.id} завершився {template_task.recurrence_end_date}. Новий екземпляр не створюється.")
            return False

        if not interval:  # Не вказано інтервал повторення
            logger.warning(
                f"Для шаблону ID {template_task.id} не вказано інтервал повторення. Новий екземпляр не створюється.")
            return False

        if not last_created_at:  # Ще не було створено жодного екземпляра
            # Перший екземпляр створюється, якщо поточний час >= дата початку шаблону.
            # Або, якщо шаблон має конкретний час початку (наприклад, due_date шаблону є першим due_date),
            # то _calculate_next_due_date має це врахувати для першого екземпляра.
            # Для простоти, якщо last_created_at is None, і ми пройшли start_date, створюємо.
            return True

            # Спрощена логіка для прикладу (ПОТРЕБУЄ ЗАМІНИ НА НАДІЙНУ БІБЛІОТЕКУ)
        if interval == RECURRENCE_DAILY:
            return last_created_at.date() < current_time.date()
        elif interval == RECURRENCE_WEEKLY:
            return last_created_at.date() <= current_time.date() - timedelta(days=7)
        elif interval == RECURRENCE_MONTHLY:
            # Дуже спрощено: якщо пройшов місяць з дня last_created_at.
            # Наприклад, якщо last_created_at було 15 січня, новий екземпляр буде 15 лютого.
            # Це не враховує дні місяця (напр. 31 число).
            # Потрібна бібліотека типу dateutil.rrule для правильного розрахунку.
            expected_next_month = last_created_at.month % 12 + 1
            expected_next_year = last_created_at.year + (1 if last_created_at.month == 12 else 0)
            if current_time.year > expected_next_year: return True
            if current_time.year == expected_next_year and current_time.month >= expected_next_month:
                return current_time.day >= last_created_at.day
            return False

        logger.warning(f"Невідомий або необроблений інтервал повторення '{interval}' для шаблону ID {template_task.id}")
        return False

    async def _calculate_next_due_date(self, template_task: Task, reference_date: datetime) -> Optional[datetime]:
        """
        [ЗАГЛУШКА/TODO] Розраховує наступну дату виконання для екземпляра повторюваного завдання.
        Це складна логіка, яка залежить від `recurrence_pattern` та `recurrence_interval`.
        """
        # TODO: Реалізувати надійний розрахунок дати на основі recurrence_pattern (RRule, cron) та last_instance_created_at.
        #  Врахувати instance_duration_days або час з шаблону `due_date`.
        #  Використати `dateutil.rrule` або подібну бібліотеку.

        # Приклад дуже спрощеної логіки: наступний день від reference_date (коли планувальник запустився),
        # з часом виконання, взятим з шаблону, або опівночі.

        instance_due_time = template_task.due_date.time() if template_task.due_date else datetime.min.time().replace(
            hour=23, minute=59, second=59)

        # Якщо це перший екземпляр і шаблон має start_date/due_date, можливо, перша дата має бути саме вона.
        if not template_task.last_instance_created_at and template_task.due_date and template_task.due_date > reference_date:
            return template_task.due_date  # Перший екземпляр успадковує due_date шаблону, якщо він у майбутньому.

        # Проста логіка: наступний день від reference_date, або + інтервал
        # Це не враховує складні правила, такі як "кожен понеділок" або "останній день місяця".
        if template_task.recurrence_interval == RECURRENCE_DAILY:
            next_day = (template_task.last_instance_created_at or reference_date).date() + timedelta(days=1)
        elif template_task.recurrence_interval == RECURRENCE_WEEKLY:
            next_day = (template_task.last_instance_created_at or reference_date).date() + timedelta(weeks=1)
        # ... і так далі для MONTHLY, YEARLY (потребує dateutil.relativedelta)
        else:  # Невідомий або простий інтервал, додаємо 1 день як запасний варіант
            logger.warning(
                f"Не вдалося точно розрахувати дату для інтервалу '{template_task.recurrence_interval}'. Використання +1 день.")
            next_day = (template_task.last_instance_created_at or reference_date).date() + timedelta(days=1)

        return datetime.combine(next_day, instance_due_time, tzinfo=timezone.utc)

    async def send_task_reminders(self) -> int:
        """
        [ЗАГЛУШКА/TODO] Надсилає нагадування про завдання, термін виконання яких наближається.
        Цей метод має викликатися періодично.
        """
        logger.info("Надсилання нагадувань про завдання (заглушка)...")
        now = datetime.now(timezone.utc)
        reminders_sent_count = 0

        # TODO: Визначити вікно для нагадувань (наприклад, за 24 години до due_date) з налаштувань.
        reminder_window_start = now  # Початок вікна - зараз
        reminder_window_end = now + timedelta(days=1)  # Кінець вікна - через 1 день

        # Запит для вибору завдань, що потребують нагадування
        # Потрібно враховувати поле `last_reminder_sent_at` в Task, щоб не надсилати повторно.
        stmt = select(Task).join(Status, Task.status_id == Status.id).where(
            Task.due_date.is_not(None),  # type: ignore
            Task.due_date >= reminder_window_start,
            Task.due_date <= reminder_window_end,
            Task.is_active == True,
            Status.code.notin_([COMPLETION_STATUS_COMPLETED, COMPLETION_STATUS_REJECTED, "CANCELLED"]),  # type: ignore
            # Умова, щоб не надсилати нагадування занадто часто (наприклад, не частіше ніж раз на 23 години)
            (Task.last_reminder_sent_at.is_(None) | (Task.last_reminder_sent_at < (now - timedelta(hours=23))))
            # type: ignore
        ).options(
            selectinload(Task.assignments).options(
                selectinload(TaskAssignment.user).options(selectinload(User.user_type))
            ),
            selectinload(Task.group)
        )
        tasks_to_remind_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        if not tasks_to_remind_db:
            logger.info("Немає завдань для надсилання нагадувань на даний момент.")
            return 0

        # from backend.app.src.services.notifications.notification import NotificationService # Локальний імпорт
        # notification_service = NotificationService(self.db_session)

        for task in tasks_to_remind_db:
            if not task.assignments:
                logger.debug(
                    f"Завдання ID {task.id} ('{task.title}') не має призначених виконавців. Пропуск нагадування.")
                continue

            for assignment in task.assignments:
                if assignment.is_active and assignment.user:
                    try:
                        logger.info(
                            f"[ЗАГЛУШКА] Надсилання нагадування для завдання ID {task.id} ('{task.title}') користувачу ID {assignment.user_id}.")
                        # TODO: Створити та надіслати сповіщення через NotificationService
                        # context_data = {"task_title": task.title, "due_date": task.due_date.strftime("%Y-%m-%d %H:%M"),
                        #                 "group_name": task.group.name if task.group else "N/A"}
                        # await notification_service.create_notification_from_template(
                        #     template_name="TASK_DEADLINE_REMINDER", # Потрібен такий шаблон
                        #     user_id=assignment.user_id,
                        #     context_data=context_data
                        # )
                        reminders_sent_count += 1
                        task.last_reminder_sent_at = now  # Оновлюємо час останнього нагадування
                        self.db_session.add(task)
                    except Exception as e:
                        logger.error(
                            f"Помилка надсилання нагадування для завдання ID {task.id} користувачу ID {assignment.user_id}: {e}",
                            exc_info=global_settings.DEBUG)
                        # Не зупиняємо весь процес через помилку одного нагадування

        if reminders_sent_count > 0:
            try:
                await self.commit()
                logger.info(
                    f"Успішно надіслано {reminders_sent_count} нагадувань про завдання та оновлено позначки часу.")
            except Exception as e:
                logger.error(f"Помилка коміту оновлень часу нагадувань: {e}", exc_info=global_settings.DEBUG)
                await self.rollback()  # Відкат, якщо не вдалося зберегти оновлення `last_reminder_sent_at`
        else:
            logger.info("Не було надіслано жодного нагадування про завдання цього разу.")

        return reminders_sent_count


logger.debug(f"{TaskSchedulingService.__name__} (сервіс планування завдань) успішно визначено.")
