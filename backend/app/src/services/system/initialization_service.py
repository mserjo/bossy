# backend/app/src/services/system/initialization_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `InitializationService` для початкового
заповнення бази даних необхідними даними при першому запуску системи
або за спеціальним запитом.
"""
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import text # type: ignore
from typing import Dict, Any, Optional

from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger
from backend.app.src.core.constants import (
    ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE, ROLE_USER_CODE,
    USER_TYPE_SUPERADMIN, USER_TYPE_BOT,
    SYSTEM_USER_ODIN_USERNAME, SYSTEM_USER_SHADOW_USERNAME,
    # Загальні статуси
    STATUS_CREATED_CODE, STATUS_ACTIVE_CODE, STATUS_INACTIVE_CODE, STATUS_PENDING_CODE,
    STATUS_COMPLETED_CODE, STATUS_REJECTED_CODE, STATUS_CANCELLED_CODE, STATUS_BLOCKED_CODE,
    # Статуси завдань (деякі можуть збігатися з загальними, але для ясності можна використовувати специфічні префікси)
    TASK_STATUS_NEW_CODE, TASK_STATUS_IN_PROGRESS_CODE, TASK_STATUS_PENDING_REVIEW_CODE,
    # Використовуємо загальний STATUS_COMPLETED_CODE для виконаних завдань, або специфічний, якщо є відмінності
    # TASK_STATUS_COMPLETED_CODE, # Вже є як STATUS_COMPLETED_CODE
    # TASK_STATUS_REJECTED_CODE,  # Вже є як STATUS_REJECTED_CODE
    # TASK_STATUS_CANCELLED_CODE, # Вже є як STATUS_CANCELLED_CODE
    # TASK_STATUS_BLOCKED_CODE,   # Вже є як STATUS_BLOCKED_CODE
    # Статуси запрошень
    INVITATION_STATUS_PENDING_CODE, INVITATION_STATUS_ACCEPTED_CODE, INVITATION_STATUS_REJECTED_CODE,
    INVITATION_STATUS_EXPIRED_CODE, INVITATION_STATUS_CANCELLED_CODE,
    # Типи груп
    GROUP_TYPE_FAMILY_CODE, GROUP_TYPE_DEPARTMENT_CODE, GROUP_TYPE_ORGANIZATION_CODE, GROUP_TYPE_GENERIC_CODE,
    # Типи завдань
    TASK_TYPE_TASK_CODE, TASK_TYPE_EVENT_CODE, TASK_TYPE_PENALTY_CODE,
    TASK_TYPE_SUBTASK_CODE, TASK_TYPE_COMPLEX_TASK_CODE, TASK_TYPE_TEAM_TASK_CODE, # Додано типи завдань
    BONUS_TYPE_POINTS_CODE, BONUS_TYPE_STARS_CODE,
    INTEGRATION_TYPE_TELEGRAM_CODE, INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE, INTEGRATION_TYPE_SLACK_CODE,
    REPORT_STATUS_QUEUED, REPORT_STATUS_PROCESSING, REPORT_STATUS_COMPLETED, REPORT_STATUS_FAILED,
    TASK_PROPOSAL_STATUS_PENDING_CODE, TASK_PROPOSAL_STATUS_APPROVED_CODE, TASK_PROPOSAL_STATUS_REJECTED_CODE
)
# Репозиторії
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository
from backend.app.src.repositories.dictionaries.group_type_repository import GroupTypeRepository
from backend.app.src.repositories.dictionaries.task_type_repository import TaskTypeRepository
from backend.app.src.repositories.dictionaries.bonus_type_repository import BonusTypeRepository
from backend.app.src.repositories.dictionaries.integration_type_repository import IntegrationTypeRepository
# from backend.app.src.repositories.dictionaries.user_type_repository import UserTypeRepository # Якщо потрібен окремий довідник
from backend.app.src.repositories.auth.user_repository import UserRepository
# Схеми Create
from backend.app.src.schemas.dictionaries.status import StatusCreateSchema
from backend.app.src.schemas.dictionaries.user_role import UserRoleCreateSchema
from backend.app.src.schemas.dictionaries.group_type import GroupTypeCreateSchema
from backend.app.src.schemas.dictionaries.task_type import TaskTypeCreateSchema
from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeCreateSchema
from backend.app.src.schemas.dictionaries.integration_type import IntegrationTypeCreateSchema
# from backend.app.src.schemas.dictionaries.user_type import UserTypeCreateSchema # Якщо потрібен окремий довідник
from backend.app.src.schemas.auth.user import UserCreateSchema
# Сервіси (для створення користувачів з хешуванням паролю)
from backend.app.src.services.auth.user_service import UserService


class InitializationService:
    """
    Сервіс для ініціалізації системи початковими даними.
    """
    def __init__(self, db_session: AsyncSession): # Приймаємо сесію в конструктор
        self.db = db_session
        self.status_repo = StatusRepository(db_session)
        self.user_role_repo = UserRoleRepository(db_session)
        self.group_type_repo = GroupTypeRepository(db_session)
        self.task_type_repo = TaskTypeRepository(db_session)
        self.bonus_type_repo = BonusTypeRepository(db_session)
        self.integration_type_repo = IntegrationTypeRepository(db_session)
        # self.user_type_repo = UserTypeRepository(db_session) # Якщо є
        self.user_repo = UserRepository(db_session)
        self.user_service = UserService(db_session) # Ініціалізуємо сервіс користувачів

    async def _init_dictionary_item(self, repo, schema_create, code, name, description=None, extra_fields=None):
        """Допоміжний метод для ініціалізації запису в довіднику."""
        if not await repo.get_by_code(code=code): # Передаємо db через self
            data_to_create = {"name": name, "code": code}
            if description is not None: # Додаємо опис тільки якщо він є
                data_to_create["description"] = description
            if extra_fields:
                data_to_create.update(extra_fields)

            await repo.create(obj_in=schema_create(**data_to_create))
            logger.info(f"Довідник '{repo.model.__name__}': створено запис '{name}' (код: {code})")

    async def init_dictionaries(self) -> Dict[str, int]:
        """Ініціалізує довідники системи. Повертає кількість створених записів по кожному типу."""
        logger.info("Початок ініціалізації довідників...")
        counts = {
            "statuses": 0, "user_roles": 0, "group_types": 0,
            "task_types": 0, "bonus_types": 0, "integration_types": 0
        }

        statuses_to_init = [
            (STATUS_CREATED_CODE, "Створено"),
            (STATUS_ACTIVE_CODE, "Активний"),
            (STATUS_INACTIVE_CODE, "Неактивний"),
            (STATUS_PENDING_CODE, "В очікуванні"),
            (STATUS_COMPLETED_CODE, "Завершено/Підтверджено"), # Може використовуватися для завдань, пропозицій тощо.
            (STATUS_REJECTED_CODE, "Відхилено"),    # Може використовуватися для завдань, пропозицій тощо.
            (STATUS_CANCELLED_CODE, "Скасовано"),   # Може використовуватися для завдань, запрошень тощо.
            (STATUS_BLOCKED_CODE, "Заблоковано"),   # Може використовуватися для завдань, користувачів тощо.
            # Специфічні статуси для завдань (якщо вони відрізняються від загальних або для більшої ясності)
            (TASK_STATUS_NEW_CODE, "Нове (завдання)"),
            (TASK_STATUS_IN_PROGRESS_CODE, "В роботі (завдання)"),
            (TASK_STATUS_PENDING_REVIEW_CODE, "На перевірці (завдання)"),
            # Для виконаних, відхилених, скасованих, заблокованих завдань можна використовувати загальні статуси
            # STATUS_COMPLETED_CODE, STATUS_REJECTED_CODE, STATUS_CANCELLED_CODE, STATUS_BLOCKED_CODE
            # або створити нові, якщо потрібна гранулярність (наприклад, TASK_STATUS_VERIFIED_BY_ADMIN)

            # Статуси запрошень
            (INVITATION_STATUS_PENDING_CODE, "Надіслано (запрошення)"),
            (INVITATION_STATUS_ACCEPTED_CODE, "Прийнято (запрошення)"),
            (INVITATION_STATUS_REJECTED_CODE, "Відхилено (запрошення)"),
            (INVITATION_STATUS_EXPIRED_CODE, "Прострочено (запрошення)"),
            (INVITATION_STATUS_CANCELLED_CODE, "Скасовано (запрошення)"),
            # Статуси звітів
            (REPORT_STATUS_QUEUED, "В черзі (звіт)"), (REPORT_STATUS_PROCESSING, "Генерується (звіт)"),
            (REPORT_STATUS_COMPLETED, "Готовий (звіт)"), (REPORT_STATUS_FAILED, "Помилка (звіт)"),
            (TASK_PROPOSAL_STATUS_PENDING_CODE, "На розгляді (пропозиція)"),
            (TASK_PROPOSAL_STATUS_APPROVED_CODE, "Прийнято (пропозиція)"),
            (TASK_PROPOSAL_STATUS_REJECTED_CODE, "Відхилено (пропозиція)"),
        ]
        for code, name in statuses_to_init:
            await self._init_dictionary_item(self.status_repo, StatusCreateSchema, code, name)
            counts["statuses"] +=1

        roles_to_init = [
            (ROLE_SUPERADMIN_CODE, "Супер Адміністратор", "Повний доступ до системи"),
            (ROLE_ADMIN_CODE, "Адміністратор Групи", "Управління групою та її учасниками"),
            (ROLE_USER_CODE, "Учасник Групи", "Звичайний користувач в групі"),
        ]
        for code, name, desc in roles_to_init:
            await self._init_dictionary_item(self.user_role_repo, UserRoleCreateSchema, code, name, desc)
            counts["user_roles"] +=1

        group_types_to_init = [
            (GROUP_TYPE_FAMILY_CODE, "Сім'я", "Для сімейних груп", {"can_have_hierarchy": False}),
            (GROUP_TYPE_DEPARTMENT_CODE, "Відділ", "Для робочих відділів", {"can_have_hierarchy": True}),
            (GROUP_TYPE_ORGANIZATION_CODE, "Організація", "Для організацій", {"can_have_hierarchy": True}),
            (GROUP_TYPE_GENERIC_CODE, "Загальна група", "Група загального призначення", {"can_have_hierarchy": True}),
        ]
        for code, name, desc, extra in group_types_to_init:
            await self._init_dictionary_item(self.group_type_repo, GroupTypeCreateSchema, code, name, desc, extra)
            counts["group_types"] +=1

        task_types_to_init = [
            (TASK_TYPE_TASK_CODE, "Завдання", "Звичайне завдання", {"is_event": False, "can_have_subtasks": True}),
            (TASK_TYPE_SUBTASK_CODE, "Підзавдання", "Частина більшого завдання", {"is_event": False, "can_have_subtasks": False}),
            (TASK_TYPE_COMPLEX_TASK_CODE, "Складне завдання", "Завдання з підзавданнями", {"is_event": False, "can_have_subtasks": True}),
            (TASK_TYPE_TEAM_TASK_CODE, "Командне завдання", "Завдання для виконання командою", {"is_event": False, "can_have_subtasks": True}),
            (TASK_TYPE_EVENT_CODE, "Подія", "Подія, що не потребує активного виконання", {"is_event": True}),
            (TASK_TYPE_PENALTY_CODE, "Штраф", "Автоматичний штраф або штрафне завдання", {"is_event": True, "is_penalty_type": True}),
        ]
        for code, name, desc, extra in task_types_to_init:
            await self._init_dictionary_item(self.task_type_repo, TaskTypeCreateSchema, code, name, desc, extra)
            counts["task_types"] +=1

        bonus_types_to_init = [
            (BONUS_TYPE_POINTS_CODE, "Бали", "Стандартні бали/очки", {"allow_decimal": False}),
            (BONUS_TYPE_STARS_CODE, "Зірочки", "Альтернативна валюта - зірочки", {"allow_decimal": False}),
        ]
        for code, name, desc, extra in bonus_types_to_init:
            await self._init_dictionary_item(self.bonus_type_repo, BonusTypeCreateSchema, code, name, desc, extra)
            counts["bonus_types"] +=1

        integration_types_to_init = [
            (INTEGRATION_TYPE_TELEGRAM_CODE, "Telegram Bot", "Інтеграція з Telegram ботом", {"category": "messenger"}),
            (INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE, "Google Calendar", "Інтеграція з Google Календарем", {"category": "calendar"}),
            (INTEGRATION_TYPE_SLACK_CODE, "Slack", "Інтеграція зі Slack", {"category": "messenger"}),
        ]
        for code, name, desc, extra in integration_types_to_init:
            await self._init_dictionary_item(self.integration_type_repo, IntegrationTypeCreateSchema, code, name, desc, extra)
            counts["integration_types"] +=1

        logger.info("Ініціалізація довідників завершена.")
        return counts

    async def init_system_users(self) -> Dict[str, bool]:
        """Створює системних користувачів (odin, shadow), якщо їх ще немає."""
        logger.info("Перевірка/створення системних користувачів...")
        results = {"odin_created": False, "shadow_created": False}

        # Odin (Superuser)
        # Використовуємо settings.auth.SUPERUSER_EMAIL та settings.auth.SUPERUSER_PASSWORD
        superuser_email_str = str(settings.auth.SUPERUSER_EMAIL) # Конвертуємо EmailStr в str для get_by_email, якщо потрібно
        odin = await self.user_repo.get_by_email(email=superuser_email_str)
        if not odin:
            if not settings.auth.SUPERUSER_PASSWORD: # Це поле обов'язкове, Pydantic вже б видав помилку
                logger.error(f"Пароль супер-адміністратора для {settings.auth.SUPERUSER_EMAIL} (SUPERUSER_PASSWORD) не встановлено в конфігурації. Неможливо створити '{SYSTEM_USER_ODIN_USERNAME}'.")
            else:
                odin_in = UserCreateSchema(
                    email=settings.auth.SUPERUSER_EMAIL, # Тут можна використовувати EmailStr
                    password=settings.auth.SUPERUSER_PASSWORD,
                    name=SYSTEM_USER_ODIN_USERNAME,
                    first_name="System", last_name="Superuser",
                    user_type_code=USER_TYPE_SUPERADMIN, # Код типу користувача
                    role_code=ROLE_SUPERADMIN_CODE, # Код ролі
                    is_email_verified=True, is_active=True
                )
                await self.user_service.create_user(obj_in=odin_in)
                logger.info(f"Супер-адміністратора '{SYSTEM_USER_ODIN_USERNAME}' ({settings.auth.SUPERUSER_EMAIL}) створено.")
                results["odin_created"] = True
        else:
            logger.info(f"Супер-адміністратор '{SYSTEM_USER_ODIN_USERNAME}' ({settings.auth.SUPERUSER_EMAIL}) вже існує.")

        # Shadow (System Bot)
        shadow_email = f"{SYSTEM_USER_SHADOW_USERNAME.lower()}@system.local" # Унікальний email для бота
        shadow = await self.user_repo.get_by_email(email=shadow_email)
        if not shadow:
            # Ботам зазвичай не потрібен пароль для входу, але модель може вимагати
            # Можна генерувати випадковий довгий пароль або використовувати спеціальне значення
            import secrets
            shadow_password = secrets.token_urlsafe(32)
            shadow_in = UserCreateSchema(
                email=shadow_email,
                password=shadow_password, # Встановлюємо пароль
                name=SYSTEM_USER_SHADOW_USERNAME,
                first_name="System", last_name="Bot",
                user_type_code=USER_TYPE_BOT,
                role_code=ROLE_USER_CODE, # TODO: Розглянути створення спеціальної ролі "bot" або "system"
                                          # для більшого контролю над правами системного бота,
                                          # якщо ROLE_USER_CODE надає занадто багато або занадто мало прав
                                          # для виконання системних завдань.
                is_active=True, is_email_verified=True # Боти активні та верифіковані за замовчуванням
            )
            await self.user_service.create_user(obj_in=shadow_in)
            logger.info(f"Системного бота '{SYSTEM_USER_SHADOW_USERNAME}' ({shadow_email}) створено.")
            results["shadow_created"] = True
        else:
            logger.info(f"Системний бот '{SYSTEM_USER_SHADOW_USERNAME}' вже існує.")
        return results

    async def run_full_initialization(self) -> Dict[str, Any]:
        """Запускає всі необхідні кроки ініціалізації в одній транзакції (по можливості)."""
        logger.info("Початок повної ініціалізації системи...")
        # Для забезпечення транзакційності, _init_dictionary_item не повинен робити commit.
        # Commit має бути тут, після всіх операцій.
        # Однак, поточна структура репозиторіїв передбачає commit в кожному методі create.
        # Це потребувало б рефакторингу репозиторіїв або передачі `commit_on_create=False`.
        # Поки що залишимо як є (кожен довідник - окрема транзакція).

        # await self.db.begin() # Початок транзакції, якщо репозиторії це підтримують
        # try:
        dict_results = await self.init_dictionaries()
        user_results = await self.init_system_users()
            # ... інші кроки ініціалізації ...
            # await self.db.commit() # Фіксація транзакції
        #     logger.info("Повна ініціалізація системи успішно завершена та зафіксована.")
        # except Exception as e:
        #     await self.db.rollback() # Відкат у разі помилки
        #     logger.error(f"Помилка під час повної ініціалізації, виконано відкат: {e}", exc_info=True)
        #     raise

        logger.info("Повна ініціалізація системи завершена.")
        return {"dictionaries": dict_results, "system_users": user_results}

# Екземпляр сервісу не створюємо тут, він буде створюватися в API ендпоінті з сесією.
