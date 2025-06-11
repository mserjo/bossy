# backend/app/src/services/system/initialization.py
# import logging # Замінено на централізований логер
from typing import Dict, Any, List, Type
from uuid import UUID # Не використовується прямо, але може бути в моделях

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError # Для обробки можливих помилок дублювання ключів

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.bonus_types import BonusType
from backend.app.src.models.dictionaries.statuses import Status # Додано для ініціалізації статусів

from backend.app.src.core.security import get_password_hash # Для хешування паролів системних користувачів
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для отримання паролів системних користувачів

# --- Визначення даних за замовчуванням ---
# Ці дані також можуть бути завантажені з конфігураційного файлу (наприклад, YAML, JSON)

DEFAULT_USER_ROLES = [
    {"name": "Суперкористувач", "code": "SUPERUSER", "description": "Повний доступ до системи."}, # i18n
    {"name": "Адміністратор", "code": "ADMIN", "description": "Доступ до адміністрування груп."}, # i18n
    {"name": "Користувач", "code": "USER", "description": "Стандартний доступ користувача в межах групи."}, # i18n
    {"name": "Гість", "code": "GUEST", "description": "Обмежений доступ для перегляду."}, # i18n
]

DEFAULT_USER_TYPES = [
    {"name": "Суперкористувач Системи", "code": "SUPERUSER_TYPE", "description": "Системний суперкористувач."}, # i18n
    {"name": "Адміністратор Платформи", "code": "ADMIN_TYPE", "description": "Адміністратор платформи/групи."}, # i18n
    {"name": "Звичайний Користувач", "code": "USER_TYPE", "description": "Звичайний користувач платформи."}, # i18n
    {"name": "Системний Бот", "code": "BOT_TYPE", "description": "Автоматизований системний агент."}, # i18n
]

DEFAULT_GROUP_TYPES = [
    {"name": "Сім'я", "code": "FAMILY", "description": "Для сімейних груп."}, # i18n
    {"name": "Відділ", "code": "DEPARTMENT", "description": "Для робочих відділів або команд."}, # i18n
    {"name": "Організація", "code": "ORGANIZATION", "description": "Для великих організацій."}, # i18n
    {"name": "Друзі", "code": "FRIENDS", "description": "Для груп друзів."}, # i18n
    {"name": "Проект", "code": "PROJECT", "description": "Для проектних груп."}, # i18n
]

DEFAULT_TASK_TYPES = [
    {"name": "Звичайне Завдання", "code": "REGULAR", "description": "Стандартне завдання."}, # i18n
    {"name": "Складне Завдання", "code": "COMPLEX", "description": "Завдання, що може вимагати кількох кроків або більших зусиль."}, # i18n
    {"name": "Подія", "code": "EVENT", "description": "Запланована подія або активність."}, # i18n
    {"name": "Доручення", "code": "CHORE", "description": "Повторюване або рутинне завдання, часто пов'язане з побутом."}, # i18n
    {"name": "Нагадування", "code": "REMINDER", "description": "Простий пункт-нагадування."}, # i18n
]

DEFAULT_BONUS_TYPES = [
    {"name": "Стандартний Бонус", "code": "STANDARD_BONUS", "description": "Звичайний тип бонусних балів."}, # i18n
    {"name": "Бонус за Досягнення", "code": "ACHIEVEMENT_BONUS", "description": "Бонус, що надається за конкретні досягнення."}, # i18n
    {"name": "Штрафні Бали", "code": "PENALTY_POINTS", "description": "Бали, що списуються як штраф.", "is_penalty": True}, # i18n
]

DEFAULT_STATUSES = [
    {"name": "Новий", "code": "NEW", "entity_type": "TASK", "description": "Завдання щойно створено."}, # i18n
    {"name": "В роботі", "code": "IN_PROGRESS", "entity_type": "TASK", "description": "Завдання виконується."}, # i18n
    {"name": "Завершено", "code": "COMPLETED", "entity_type": "TASK", "description": "Завдання успішно виконано."}, # i18n
    {"name": "Ухвалено", "code": "APPROVED", "entity_type": "TASK_COMPLETION", "description": "Виконання завдання ухвалено."}, # i18n
    {"name": "Відхилено", "code": "REJECTED", "entity_type": "TASK_COMPLETION", "description": "Виконання завдання відхилено."}, # i18n
    {"name": "Активний", "code": "ACTIVE", "entity_type": "USER", "description": "Обліковий запис користувача активний."}, # i18n
    {"name": "Неактивний", "code": "INACTIVE", "entity_type": "USER", "description": "Обліковий запис користувача неактивний."}, # i18n
    {"name": "В очікуванні", "code": "PENDING", "entity_type": "INVITATION", "description": "Запрошення очікує на відповідь."}, # i18n
    {"name": "Прийнято", "code": "ACCEPTED", "entity_type": "INVITATION", "description": "Запрошення прийнято."}, # i18n
]

# TODO: Паролі для системних користувачів повинні завантажуватися з конфігурації (settings.py або змінні середовища)
#  і бути складними. Наголосити на необхідності їх зміни після першого запуску.
DEFAULT_SYSTEM_USERS = [
    {
        "username": "odin", "email": getattr(settings, "ODIN_USER_EMAIL", "odin@system.local"),
        "password": getattr(settings, "ODIN_USER_PASSWORD", "ChangeThisOdin!"),
        "full_name": "Odin Superuser", "is_superuser": True, "is_active": True, "is_verified": True,
        "user_type_code": "SUPERUSER_TYPE", "user_role_codes": ["SUPERUSER"]
    },
    {
        "username": "shadow", "email": getattr(settings, "SHADOW_USER_EMAIL", "shadow@system.local"),
        "password": getattr(settings, "SHADOW_USER_PASSWORD", "ChangeThisShadow!"),
        "full_name": "Shadow System Bot", "is_superuser": False, "is_active": True, "is_verified": True,
        "user_type_code": "BOT_TYPE", "user_role_codes": ["ADMIN"] # Бот може мати адмінські права для системних завдань
    },
    {
        "username": "root", "email": getattr(settings, "ROOT_USER_EMAIL", "root@system.local"),
        "password": getattr(settings, "ROOT_USER_PASSWORD", "ChangeThisRoot!"),
        "full_name": "Root Superuser", "is_superuser": True, "is_active": True, "is_verified": True,
        "user_type_code": "SUPERUSER_TYPE", "user_role_codes": ["SUPERUSER"]
    },
]


class InitialDataService(BaseService):
    """
    Сервіс для ініціалізації системи даними за замовчуванням.
    Включає створення попередньо визначених елементів довідників (ролі, типи) та системних користувачів.
    Методи сервісу є ідемпотентними: вони не створюють дублікатів, якщо дані вже існують.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("InitialDataService ініціалізовано.")

    async def _initialize_dictionary(self, model_cls: Type[Any], defaults: List[Dict[str, Any]], code_field: str = "code") -> int:
        """
        Загальний допоміжний метод для ініціалізації таблиці-довідника.
        Перевіряє, чи існують елементи з кодами за замовчуванням, перед створенням.
        """
        created_count = 0
        for item_data in defaults:
            code_value = item_data.get(code_field)
            if not code_value:
                logger.warning(f"Пропуск елемента в {model_cls.__name__} через відсутність значення для поля '{code_field}': {item_data}")
                continue

            existing_item = (await self.db_session.execute(
                select(model_cls.id).where(getattr(model_cls, code_field) == code_value) # type: ignore
            )).scalar_one_or_none()

            if not existing_item:
                try:
                    new_item = model_cls(**item_data)
                    self.db_session.add(new_item)
                    # Не робимо flush тут, щоб дозволити загальний rollback, якщо потрібно
                    logger.info(f"Створено {model_cls.__name__} '{item_data.get('name', code_value)}' з кодом '{code_value}'.")
                    created_count += 1
                except Exception as e: # Широкий except для логування, але помилка буде піднята далі, якщо не IntegrityError
                    # Якщо помилка IntegrityError, це може означати паралельне створення, що є прийнятним.
                    # Інші помилки можуть бути більш критичними.
                    if isinstance(e, IntegrityError):
                         logger.warning(f"Помилка цілісності (можливо, паралельне створення) для {model_cls.__name__} з кодом '{code_value}'. Пропуск.")
                         await self.db_session.rollback() # Відкат невдалого додавання
                    else:
                        logger.error(f"Помилка створення {model_cls.__name__} '{item_data.get('name', code_value)}': {e}", exc_info=True)
                        raise # Перекидаємо помилку, щоб перервати загальну ініціалізацію, якщо це не IntegrityError
            else:
                logger.info(f"{model_cls.__name__} з кодом '{code_value}' вже існує. Пропуск.")
        return created_count

    async def initialize_user_roles(self) -> int:
        """Ініціалізує ролі користувачів за замовчуванням."""
        logger.info("Ініціалізація ролей користувачів за замовчуванням...")
        count = await self._initialize_dictionary(UserRole, DEFAULT_USER_ROLES)
        logger.info(f"Завершено ініціалізацію ролей користувачів. Створено {count} нових ролей.")
        return count

    async def initialize_user_types(self) -> int:
        """Ініціалізує типи користувачів за замовчуванням."""
        logger.info("Ініціалізація типів користувачів за замовчуванням...")
        count = await self._initialize_dictionary(UserType, DEFAULT_USER_TYPES)
        logger.info(f"Завершено ініціалізацію типів користувачів. Створено {count} нових типів.")
        return count

    async def initialize_group_types(self) -> int:
        """Ініціалізує типи груп за замовчуванням."""
        logger.info("Ініціалізація типів груп за замовчуванням...")
        count = await self._initialize_dictionary(GroupType, DEFAULT_GROUP_TYPES)
        logger.info(f"Завершено ініціалізацію типів груп. Створено {count} нових типів.")
        return count

    async def initialize_task_types(self) -> int:
        """Ініціалізує типи завдань за замовчуванням."""
        logger.info("Ініціалізація типів завдань за замовчуванням...")
        count = await self._initialize_dictionary(TaskType, DEFAULT_TASK_TYPES)
        logger.info(f"Завершено ініціалізацію типів завдань. Створено {count} нових типів.")
        return count

    async def initialize_bonus_types(self) -> int:
        """Ініціалізує типи бонусів за замовчуванням."""
        logger.info("Ініціалізація типів бонусів за замовчуванням...")
        count = await self._initialize_dictionary(BonusType, DEFAULT_BONUS_TYPES)
        logger.info(f"Завершено ініціалізацію типів бонусів. Створено {count} нових типів.")
        return count

    async def initialize_statuses(self) -> int:
        """Ініціалізує статуси за замовчуванням."""
        logger.info("Ініціалізація статусів за замовчуванням...")
        count = await self._initialize_dictionary(Status, DEFAULT_STATUSES) # Використовуємо 'code' як унікальний ключ
        logger.info(f"Завершено ініціалізацію статусів. Створено {count} нових статусів.")
        return count


    async def initialize_system_users(self) -> int:
        """
        Ініціалізує системних користувачів за замовчуванням ('odin', 'shadow', 'root').
        Вимагає попередньої ініціалізації UserType та UserRole.
        """
        logger.info("Ініціалізація системних користувачів за замовчуванням...")
        created_count = 0
        for user_data in DEFAULT_SYSTEM_USERS:
            username = user_data["username"]
            email = user_data["email"]

            user_exists = (await self.db_session.execute(
                select(User.id).where(or_(User.username == username, User.email == email)) # type: ignore
            )).scalar_one_or_none()

            if user_exists:
                logger.info(f"Системний користувач '{username}' або користувач з email '{email}' вже існує. Пропуск.")
                continue

            try:
                user_type = (await self.db_session.execute(
                    select(UserType).where(UserType.code == user_data["user_type_code"]))
                ).scalar_one_or_none()
                if not user_type:
                    logger.error(f"Тип користувача '{user_data['user_type_code']}' не знайдено для системного користувача '{username}'. Пропуск.")
                    continue

                user_roles_db = (await self.db_session.execute(
                    select(UserRole).where(UserRole.code.in_(user_data.get("user_role_codes", [])))) # type: ignore
                ).scalars().all()

                if len(user_roles_db) != len(user_data.get("user_role_codes", [])):
                    found_codes = [r.code for r in user_roles_db]
                    missing_codes = [code for code in user_data.get("user_role_codes", []) if code not in found_codes]
                    logger.warning(f"Не всі ролі знайдено для '{username}'. Знайдено: {found_codes}, Відсутні: {missing_codes}.")

                new_user_db = User(
                    username=username, email=email,
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data.get("full_name"),
                    is_active=user_data.get("is_active", True),
                    is_superuser=user_data.get("is_superuser", False),
                    is_verified=user_data.get("is_verified", True),
                    user_type_id=user_type.id,
                    roles=user_roles_db
                )
                self.db_session.add(new_user_db)
                # Не робимо flush тут для загального rollback
                logger.info(f"Системного користувача '{username}' підготовлено до створення.")
                created_count += 1
            except Exception as e:
                logger.error(f"Помилка підготовки системного користувача '{username}': {e}", exc_info=True)
                # Не перекидаємо помилку, щоб спробувати створити інших системних користувачів

        logger.info(f"Завершено підготовку системних користувачів. Готово до створення: {created_count} нових користувачів.")
        return created_count

    async def _check_essential_data_exists(self) -> bool:
        """Перевіряє наявність критично важливих ролей та типів для створення системних користувачів."""
        # Перевірка наявності ролі SUPERUSER та типів SUPERUSER_TYPE, BOT_TYPE
        su_role = (await self.db_session.execute(select(UserRole.id).where(UserRole.code == "SUPERUSER"))).scalar_one_or_none()
        su_type = (await self.db_session.execute(select(UserType.id).where(UserType.code == "SUPERUSER_TYPE"))).scalar_one_or_none()
        bot_type = (await self.db_session.execute(select(UserType.id).where(UserType.code == "BOT_TYPE"))).scalar_one_or_none()
        admin_role = (await self.db_session.execute(select(UserRole.id).where(UserRole.code == "ADMIN"))).scalar_one_or_none()


        if not all([su_role, su_type, bot_type, admin_role]):
            logger.warning(f"Перевірка критичних даних: Роль SUPERUSER: {'OK' if su_role else 'ВІДСУТНЯ'}, Тип SUPERUSER_TYPE: {'OK' if su_type else 'ВІДСУТНІЙ'}, Тип BOT_TYPE: {'OK' if bot_type else 'ВІДСУТНІЙ'}, Роль ADMIN: {'OK' if admin_role else 'ВІДСУТНЯ'}") # i18n
            return False
        return True

    async def run_full_initialization(self) -> Dict[str, int]:
        """
        Виконує повну ініціалізацію всіх стандартних даних системи.
        Зміни комітяться в кінці, якщо всі кроки успішні.
        Якщо будь-який крок зазнає критичної невдачі (окрім IntegrityError при створенні словників),
        відбувається відкат всієї транзакції.
        """
        logger.info("Запуск повної ініціалізації системних даних...")
        results: Dict[str, int] = {}

        try:
            results["user_roles"] = await self.initialize_user_roles()
            results["user_types"] = await self.initialize_user_types()
            results["group_types"] = await self.initialize_group_types()
            results["task_types"] = await self.initialize_task_types()
            results["bonus_types"] = await self.initialize_bonus_types()
            results["statuses"] = await self.initialize_statuses() # Додано ініціалізацію статусів

            if not await self._check_essential_data_exists():
                # i18n
                logger.error("Критично важливі типи/ролі для створення системних користувачів відсутні після ініціалізації довідників. Ініціалізація користувачів скасована.")
                # Можна кинути виняток, якщо це критично, або просто продовжити без створення користувачів
                results["system_users"] = 0
                # raise ValueError("Не вдалося створити основні ролі/типи, необхідні для системних користувачів.")
            else:
                results["system_users"] = await self.initialize_system_users()

            await self.commit() # Єдиний коміт в кінці успішної підготовки всіх даних
            logger.info("Повна ініціалізація системних даних успішно завершена та закомічена.")

        except Exception as e:
            logger.error(f"Повна ініціалізація системних даних не вдалася: {e}", exc_info=settings.DEBUG)
            await self.rollback() # Відкат усіх змін, якщо будь-який крок спричинив непередбачену помилку
            raise # Перекидаємо помилку далі
        return results

logger.debug(f"{InitialDataService.__name__} (сервіс початкової ініціалізації) успішно визначено.")
