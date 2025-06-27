# backend/app/src/services/system/initialization_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `InitializationService` для початкового
заповнення бази даних необхідними даними при першому запуску системи
або за спеціальним запитом.
"""
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import text # type: ignore

from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger
from backend.app.src.core.constants import (
    ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE, ROLE_USER_CODE,
    USER_TYPE_SUPERADMIN, SYSTEM_USER_ODIN_USERNAME,
    STATUS_CREATED_CODE, STATUS_ACTIVE_CODE, STATUS_INACTIVE_CODE, STATUS_PENDING_CODE,
    STATUS_COMPLETED_CODE, STATUS_REJECTED_CODE, STATUS_CANCELLED_CODE, STATUS_BLOCKED_CODE,
    TASK_STATUS_NEW_CODE, TASK_STATUS_IN_PROGRESS_CODE, TASK_STATUS_PENDING_REVIEW_CODE,
    TASK_STATUS_COMPLETED_CODE as TASK_STATUS_COMPLETED_SPECIFIC_CODE, # Уникаємо конфлікту імен
    TASK_STATUS_REJECTED_CODE as TASK_STATUS_REJECTED_SPECIFIC_CODE,
    TASK_STATUS_CANCELLED_CODE as TASK_STATUS_CANCELLED_SPECIFIC_CODE,
    TASK_STATUS_BLOCKED_CODE as TASK_STATUS_BLOCKED_SPECIFIC_CODE,
    INVITATION_STATUS_PENDING_CODE, INVITATION_STATUS_ACCEPTED_CODE, INVITATION_STATUS_REJECTED_CODE,
    INVITATION_STATUS_EXPIRED_CODE, INVITATION_STATUS_CANCELLED_CODE,
    GROUP_TYPE_FAMILY_CODE, GROUP_TYPE_DEPARTMENT_CODE, GROUP_TYPE_ORGANIZATION_CODE, GROUP_TYPE_GENERIC_CODE,
    TASK_TYPE_TASK_CODE, TASK_TYPE_EVENT_CODE, TASK_TYPE_PENALTY_CODE,
    BONUS_TYPE_POINTS_CODE, BONUS_TYPE_STARS_CODE,
    INTEGRATION_TYPE_TELEGRAM_CODE, INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE, INTEGRATION_TYPE_SLACK_CODE,
    # Додайте сюди інші коди з constants.py, які потрібно ініціалізувати
    REPORT_STATUS_QUEUED, REPORT_STATUS_PROCESSING, REPORT_STATUS_COMPLETED, REPORT_STATUS_FAILED,
    TASK_PROPOSAL_STATUS_PENDING_CODE, TASK_PROPOSAL_STATUS_APPROVED_CODE, TASK_PROPOSAL_STATUS_REJECTED_CODE
)
from backend.app.src.repositories.dictionaries.status import status_repository
from backend.app.src.repositories.dictionaries.user_role import user_role_repository
from backend.app.src.repositories.dictionaries.group_type import group_type_repository
from backend.app.src.repositories.dictionaries.task_type import task_type_repository
from backend.app.src.repositories.dictionaries.bonus_type import bonus_type_repository
from backend.app.src.repositories.dictionaries.integration import integration_repository
from backend.app.src.repositories.auth.user import user_repository
from backend.app.src.schemas.dictionaries.status import StatusCreateSchema
from backend.app.src.schemas.dictionaries.user_role import UserRoleCreateSchema
from backend.app.src.schemas.dictionaries.group_type import GroupTypeCreateSchema
from backend.app.src.schemas.dictionaries.task_type import TaskTypeCreateSchema
from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeCreateSchema
from backend.app.src.schemas.dictionaries.integration_type import IntegrationTypeCreateSchema
from backend.app.src.schemas.auth.user import UserCreateSchema
from backend.app.src.core.security import get_password_hash # Для створення пароля superadmin

class InitializationService:
    """
    Сервіс для ініціалізації системи початковими даними.
    """
    async def _init_dictionary(self, db: AsyncSession, repo, schema_create, code, name, description=None, extra_fields=None):
        """Допоміжний метод для ініціалізації запису в довіднику."""
        if not await repo.get_by_code(db, code=code):
            data_to_create = {"name": name, "code": code, "description": description or name}
            if extra_fields:
                data_to_create.update(extra_fields)

            # Деякі CreateSchema можуть не приймати None для description
            if data_to_create["description"] is None:
                del data_to_create["description"] # Або встановити в ""

            await repo.create(db, obj_in=schema_create(**data_to_create))
            logger.info(f"Довідник '{repo.model.__name__}': створено запис '{name}' (код: {code})")

    async def init_dictionaries(self, db: AsyncSession) -> None:
        """Ініціалізує довідники системи."""
        logger.info("Початок ініціалізації довідників...")

        # Статуси
        statuses_to_init = [
            (STATUS_CREATED_CODE, "Створено"), (STATUS_ACTIVE_CODE, "Активний"), (STATUS_INACTIVE_CODE, "Неактивний"),
            (STATUS_PENDING_CODE, "В очікуванні"), (STATUS_COMPLETED_CODE, "Завершено/Підтверджено"),
            (STATUS_REJECTED_CODE, "Відхилено"), (STATUS_CANCELLED_CODE, "Скасовано"), (STATUS_BLOCKED_CODE, "Заблоковано"),
            (TASK_STATUS_NEW_CODE, "Нове (завдання)"), (TASK_STATUS_IN_PROGRESS_CODE, "В роботі (завдання)"),
            (TASK_STATUS_PENDING_REVIEW_CODE, "На перевірці (завдання)"),
            (TASK_STATUS_COMPLETED_SPECIFIC_CODE, "Виконано (завдання)"), # Використовуємо spezifische Konstante
            (TASK_STATUS_REJECTED_SPECIFIC_CODE, "Відхилено (завдання)"),
            (TASK_STATUS_CANCELLED_SPECIFIC_CODE, "Скасовано (завдання)"),
            (TASK_STATUS_BLOCKED_SPECIFIC_CODE, "Заблоковано (завдання)"),
            (INVITATION_STATUS_PENDING_CODE, "Надіслано (запрошення)"), (INVITATION_STATUS_ACCEPTED_CODE, "Прийнято (запрошення)"),
            (INVITATION_STATUS_REJECTED_CODE, "Відхилено (запрошення)"), (INVITATION_STATUS_EXPIRED_CODE, "Прострочено (запрошення)"),
            (INVITATION_STATUS_CANCELLED_CODE, "Скасовано (запрошення)"),
            (REPORT_STATUS_QUEUED, "В черзі (звіт)"), (REPORT_STATUS_PROCESSING, "Генерується (звіт)"),
            (REPORT_STATUS_COMPLETED, "Готовий (звіт)"), (REPORT_STATUS_FAILED, "Помилка (звіт)"),
            (TASK_PROPOSAL_STATUS_PENDING_CODE, "На розгляді (пропозиція)"),
            (TASK_PROPOSAL_STATUS_APPROVED_CODE, "Прийнято (пропозиція)"),
            (TASK_PROPOSAL_STATUS_REJECTED_CODE, "Відхилено (пропозиція)"),
        ]
        for code, name in statuses_to_init:
            await self._init_dictionary(db, status_repository, StatusCreateSchema, code, name)

        # Ролі користувачів
        roles_to_init = [
            (ROLE_SUPERADMIN_CODE, "Супер Адміністратор", "Повний доступ до системи"),
            (ROLE_ADMIN_CODE, "Адміністратор Групи", "Управління групою та її учасниками"),
            (ROLE_USER_CODE, "Учасник Групи", "Звичайний користувач в групі"),
        ]
        for code, name, desc in roles_to_init:
            await self._init_dictionary(db, user_role_repository, UserRoleCreateSchema, code, name, desc)

        # Типи груп
        group_types_to_init = [
            (GROUP_TYPE_FAMILY_CODE, "Сім'я", "Для сімейних груп", {"can_have_hierarchy": False}), # Приклад extra_fields
            (GROUP_TYPE_DEPARTMENT_CODE, "Відділ", "Для робочих відділів", {"can_have_hierarchy": True}),
            (GROUP_TYPE_ORGANIZATION_CODE, "Організація", "Для організацій з можливою ієрархією", {"can_have_hierarchy": True}),
            (GROUP_TYPE_GENERIC_CODE, "Загальна група", "Група загального призначення", {"can_have_hierarchy": True}),
        ]
        for code, name, desc, extra in group_types_to_init:
            await self._init_dictionary(db, group_type_repository, GroupTypeCreateSchema, code, name, desc, extra)

        # Типи завдань/подій
        task_types_to_init = [
            (TASK_TYPE_TASK_CODE, "Завдання", "Звичайне завдання", {"is_event": False, "can_have_subtasks": True}),
            (TASK_TYPE_EVENT_CODE, "Подія", "Подія, що не потребує активного виконання", {"is_event": True}),
            (TASK_TYPE_PENALTY_CODE, "Штрафне завдання", "Завдання, що призводить до штрафу", {"is_penalty_type": True}),
            # Додайте TASK_TYPE_SUBTASK_CODE, TASK_TYPE_COMPLEX_TASK_CODE, TASK_TYPE_TEAM_TASK_CODE, якщо вони окремі типи
        ]
        for code, name, desc, extra in task_types_to_init:
            await self._init_dictionary(db, task_type_repository, TaskTypeCreateSchema, code, name, desc, extra)

        # Типи бонусів
        bonus_types_to_init = [
            (BONUS_TYPE_POINTS_CODE, "Бали", "Стандартні бали/очки", {"allow_decimal": False}),
            (BONUS_TYPE_STARS_CODE, "Зірочки", "Альтернативна валюта - зірочки", {"allow_decimal": False}),
        ]
        for code, name, desc, extra in bonus_types_to_init:
            await self._init_dictionary(db, bonus_type_repository, BonusTypeCreateSchema, code, name, desc, extra)

        # Типи інтеграцій
        integration_types_to_init = [
            (INTEGRATION_TYPE_TELEGRAM_CODE, "Telegram Bot", "Інтеграція з Telegram ботом", {"category": "messenger"}),
            (INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE, "Google Calendar", "Інтеграція з Google Календарем", {"category": "calendar"}),
            (INTEGRATION_TYPE_SLACK_CODE, "Slack", "Інтеграція зі Slack", {"category": "messenger"}),
        ]
        for code, name, desc, extra in integration_types_to_init:
            await self._init_dictionary(db, integration_repository, IntegrationTypeCreateSchema, code, name, desc, extra)

        logger.info("Ініціалізація довідників завершена.")


    async def init_superuser(self, db: AsyncSession) -> None:
        """Створює супер-адміністратора, якщо його ще немає."""
        logger.info("Перевірка/створення супер-адміністратора...")
        superuser = await user_repository.get_by_email(db, email=settings.auth.SUPERUSER_EMAIL)
        if not superuser:
            if not settings.auth.SUPERUSER_PASSWORD:
                logger.error("Пароль супер-адміністратора (SUPERUSER_PASSWORD) не встановлено в налаштуваннях. Неможливо створити супер-адміністратора.")
                return

            superuser_in = UserCreateSchema(
                email=settings.auth.SUPERUSER_EMAIL,
                password=settings.auth.SUPERUSER_PASSWORD, # Пароль буде захешовано в сервісі
                name=SYSTEM_USER_ODIN_USERNAME, # Ім'я для супер-адміна
                first_name="System",
                last_name="Superuser",
                user_type_code=USER_TYPE_SUPERADMIN, # Встановлюємо тип
                is_email_verified=True # Супер-адмін має підтверджений email
            )
            # Використовуємо user_service для створення, він обробляє хешування пароля
            from backend.app.src.services.auth.user_service import userService
            await userService.create_user(db, obj_in=superuser_in)
            logger.info(f"Супер-адміністратора '{settings.auth.SUPERUSER_EMAIL}' створено.")
        else:
            logger.info(f"Супер-адміністратор '{settings.auth.SUPERUSER_EMAIL}' вже існує.")


    async def run_initialization(self, db: AsyncSession) -> None:
        """Запускає всі необхідні кроки ініціалізації."""
        logger.info("Початок загальної ініціалізації системи...")

        # Перевірка, чи потрібно взагалі виконувати ініціалізацію
        # Можна додати прапорець в SystemSettingsModel, який вказує, чи була вже ініціалізація.
        # Або перевіряти наявність ключових записів (наприклад, ролі супер-адміна).
        # Поки що просто виконуємо.

        # TODO: Обернути в одну транзакцію, якщо можливо і доцільно.
        #       Але _init_dictionary вже робить commit. Це треба змінити, якщо потрібна одна транзакція.
        #       Або ж, кожен _init_dictionary - це окрема маленька транзакція, що теж прийнятно.

        await self.init_dictionaries(db)
        await self.init_superuser(db)

        # TODO: Додати створення інших необхідних початкових даних:
        # - Системні налаштування за замовчуванням (в SystemSettingsModel)
        # - Шаблони сповіщень за замовчуванням (в NotificationTemplateModel)
        # - Можливо, приклади шаблонів груп (в GroupTemplateModel)

        logger.info("Загальна ініціалізація системи завершена.")


initialization_service = InitializationService()

# TODO: Розглянути, як і коли викликати `run_initialization`.
#       - При першому запуску додатку (наприклад, через startup event FastAPI, якщо немає міграцій Alembic, що це роблять).
#       - Через окрему CLI команду (наприклад, `python -m backend.app.scripts.init_db`).
#       - Як частина процесу розгортання.
#       Важливо, щоб це виконувалося лише один раз або було ідемпотентним.
#       Метод `_init_dictionary` вже ідемпотентний (перевіряє існування за кодом).
#       Метод `init_superuser` також ідемпотентний.
#
# TODO: Переконатися, що всі необхідні константи імпортовані та використовуються.
#       Зокрема, для всіх довідників, які мають бути заповнені.
#
# TODO: Переконатися, що схеми Create для довідників приймають `description` та інші
#       поля, які передаються в `_init_dictionary`.
#       (Так, `BaseDictCreateSchema` має `description`).
#
# Все виглядає як хороший початок для сервісу ініціалізації.
# Він покриває створення основних довідників та супер-адміністратора.
