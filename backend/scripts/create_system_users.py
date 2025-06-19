# backend/scripts/create_system_users.py
import asyncio
import os
import sys
import logging
import uuid  # Для генерації випадкових паролів, якщо потрібно

# -*- coding: utf-8 -*-
"""
Скрипт для створення або оновлення визначених системних користувачів.

Цей скрипт забезпечує наявність ключових системних облікових записів,
таких як 'odin' (суперкористувач) та 'shadow' (системний бот).
Паролі для цих користувачів беруться з змінних середовища або генеруються,
якщо не задані. Скрипт є ідемпотентним: якщо користувач вже існує,
він не буде створюватися повторно.

Для роботи скрипта необхідно, щоб довідники ролей (UserRole) та типів користувачів (UserType)
вже містили відповідні записи (наприклад, 'SUPERUSER', 'ADMIN', 'BOT').
"""
import asyncio
import os
import sys
import logging  # Стандартний модуль логування
import uuid  # Для генерації випадкових паролів

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# --- Імпорт компонентів додатку ---
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional  # Для типізації

try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта create_system_users.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для create_system_users.")  # i18n

from backend.app.src.core.database import get_db_session  # Для отримання сесії БД
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.schemas.auth.user_schemas import UserCreateSuperuserSchema, \
    UserCreateSchema  # Використовуємо обидві схеми
from backend.app.src.models.auth import User as UserModel
from backend.app.src.repositories.auth.user_repository import UserRepository
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository
from backend.app.src.repositories.dictionaries.user_type_repository import UserTypeRepository
from backend.app.src.core.constants import UserRoleEnum, UserTypeEnum


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


# --- Визначення даних системних користувачів ---
# Паролі: рекомендується встановлювати через змінні середовища.
# Якщо змінна середовища для пароля не встановлена, скрипт згенерує випадковий пароль.
SYSTEM_USERS_DATA = [
    {
        "email": os.getenv("ODIN_USER_EMAIL", "odin@kudos.system"),
        "username": "odin",
        "password_env_var": "ODIN_USER_PASSWORD",
        "first_name": "Odin",
        "last_name": "System",
        "role_code": UserRoleEnum.SUPERUSER.value,
        "type_code": UserTypeEnum.SUPERUSER.value,
        "is_superuser": True,  # Явно вказуємо
        "is_active": True,
        "is_verified": True,  # Системні користувачі верифіковані за замовчуванням
        "notes": _("Всемогутній системний суперкористувач, аналог Одіна у скандинавській міфології.")  # i18n
    },
    {
        "email": os.getenv("SHADOW_USER_EMAIL", "shadow@kudos.system"),
        "username": "shadow",
        "password_env_var": "SHADOW_USER_PASSWORD",
        "first_name": "Shadow",
        "last_name": "Bot",
        # Роль для 'shadow' може бути 'ADMIN' або спеціальна роль для ботів, наприклад 'SYSTEM_BOT'
        "role_code": UserRoleEnum.ADMIN.value,  # Або інша роль, якщо визначена
        "type_code": UserTypeEnum.BOT.value,
        "is_superuser": False,  # Shadow не є суперкористувачем
        "is_active": True,
        "is_verified": True,
        "notes": _("Системний бот для виконання фонових завдань та автоматизації, 'тіньовий' помічник.")  # i18n
    },
    {
        "email": os.getenv("ROOT_USER_EMAIL", "root@kudos.system"),
        "username": "root",  # 'root' часто асоціюється з найвищими правами
        "password_env_var": "ROOT_USER_PASSWORD",
        "first_name": "Root",
        "last_name": "Access",
        "role_code": UserRoleEnum.SUPERUSER.value,  # 'root' також суперкористувач
        "type_code": UserTypeEnum.SUPERUSER.value,  # Тип також суперкористувач
        "is_superuser": True,
        "is_active": True,
        "is_verified": True,
        "notes": _("Системний суперкористувач з максимальними правами, аналог 'root' в Unix-системах.")  # i18n
    },
]


async def create_system_user_if_not_exists(db: AsyncSession, user_data_config: Dict[str, Any]):
    """
    Створює системного користувача, якщо він ще не існує за email або username.
    Використовує відповідну схему та метод сервісу залежно від прапору `is_superuser`.

    Args:
        db: Асинхронна сесія бази даних.
        user_data_config: Словник з конфігурацією даних користувача.
    """
    user_repo = UserRepository(db_session=db)
    user_role_repo = UserRoleRepository(db_session=db)
    user_type_repo = UserTypeRepository(db_session=db)
    user_service = UserService(db_session=db)

    email = user_data_config['email']
    username = user_data_config.get('username')

    # Отримання пароля з .env або генерація нового, якщо не знайдено
    password = os.getenv(user_data_config["password_env_var"])
    generated_password_info = ""
    if not password:
        password = str(uuid.uuid4())  # Генеруємо надійний випадковий пароль
        # i18n: Critical log message - Generated password (must be saved)
        generated_password_info = _(
            "ПАРОЛЬ БУЛО ЗГЕНЕРОВАНО АВТОМАТИЧНО: '{password}'. ОБОВ'ЯЗКОВО ЗБЕРЕЖІТЬ ЦЕЙ ПАРОЛЬ У БЕЗПЕЧНОМУ МІСЦІ!").format(
            password=password)
        logger.critical(f"Для користувача {email}: {generated_password_info}")

    # i18n: Log message - Checking system user by email and username
    logger.info(_("Перевірка системного користувача: email='{email}', username='{username}'").format(email=email,
                                                                                                     username=username))

    existing_user_by_email: Optional[UserModel] = await user_repo.get_by_email(email=email)
    if existing_user_by_email:
        # i18n: Log message - System user with email already exists
        logger.info(_("Системний користувач з email '{email}' вже існує. Пропускаємо створення.").format(email=email))
        return

    if username:
        existing_user_by_username: Optional[UserModel] = await user_repo.get_by_username(username=username)
        if existing_user_by_username:
            # i18n: Log message - System user with username already exists
            logger.info(_("Системний користувач з нікнеймом '{username}' вже існує. Пропускаємо створення.").format(
                username=username))
            return

    # Отримання ID ролі та типу користувача з довідників
    user_role = await user_role_repo.get_by_code(code=user_data_config['role_code'])
    if not user_role:
        # i18n: Error message - Role not found for user
        logger.error(
            _("Помилка: Роль '{role_code}' не знайдена для користувача '{email}'. Створення скасовано.").format(
                role_code=user_data_config['role_code'], email=email))
        logger.error(
            _("Будь ласка, переконайтеся, що всі необхідні ролі (`UserRoleEnum`) завантажені в довідник (наприклад, за допомогою `backend.scripts.run_seed`)."))  # i18n
        return

    user_type = await user_type_repo.get_by_code(code=user_data_config['type_code'])
    if not user_type:
        # i18n: Error message - User type not found for user
        logger.error(
            _("Помилка: Тип користувача '{type_code}' не знайдений для '{email}'. Створення скасовано.").format(
                type_code=user_data_config['type_code'], email=email))
        logger.error(
            _("Будь ласка, переконайтеся, що всі необхідні типи (`UserTypeEnum`) завантажені в довідник."))  # i18n
        return

    # Підготовка даних для створення користувача
    user_common_data = {
        "email": email,
        "password": password,
        "first_name": user_data_config.get('first_name'),
        "last_name": user_data_config.get('last_name'),
        "username": username,
        "user_role_id": user_role.id,
        "user_type_id": user_type.id,
        "is_active": user_data_config.get('is_active', True),
        "is_verified": user_data_config.get('is_verified', True),  # Системні користувачі зазвичай верифіковані
        "notes": user_data_config.get('notes')
    }

    try:
        # i18n: Log message - Creating system user with role and type
        logger.info(
            _("Створення системного користувача: {email} з роллю '{role_code}' та типом '{type_code}'...").format(
                email=email, role_code=user_data_config['role_code'], type_code=user_data_config['type_code']
            ))

        new_user: Optional[UserModel] = None
        if user_data_config.get('is_superuser', False):
            create_schema = UserCreateSuperuserSchema(**user_common_data)
            # `create_superuser` в сервісі має сам встановити is_superuser=True
            new_user = await user_service.create_superuser(user_data=create_schema)
        else:
            # Для звичайних системних користувачів (не суперюзерів)
            create_schema = UserCreateSchema(**user_common_data)
            # Потрібен метод в UserService, який створює користувача, але не робить його суперюзером.
            # Припустимо, це `create_user` або аналогічний.
            # Якщо `create_user` очікує `UserCreateSchema`, то все гаразд.
            # Якщо `UserService.create_user` не встановлює is_superuser, то це те, що потрібно.
            new_user = await user_service.create_user(
                user_data=create_schema)  # Використовуємо загальний метод створення

        if new_user:
            # i18n: Success message - System user created
            log_msg_user_created = _("Системний користувач '{email}' (ID: {user_id}) успішно створений.").format(
                email=new_user.email, user_id=new_user.id)
            if generated_password_info:
                # Якщо пароль було згенеровано, додаємо критичне повідомлення до логу
                logger.critical(f"{log_msg_user_created} {generated_password_info}")
            else:
                logger.info(log_msg_user_created)
        else:
            # i18n: Error message - Failed to create system user
            logger.error(
                _("Не вдалося створити системного користувача {email}. Сервіс не повернув об'єкт користувача.").format(
                    email=email))

    except Exception as e:
        # i18n: Error message - Error during system user creation
        logger.error(
            _("Помилка під час створення системного користувача {email}: {error}").format(email=email, error=e),
            exc_info=True)


async def run_script_async_logic():
    """
    Асинхронна головна функція для створення всіх визначених системних користувачів.
    """
    # i18n: Log message - Starting system users creation script
    logger.info(_("Запуск скрипта створення системних користувачів..."))

    session_generator = get_db_session()
    db_session: Optional[AsyncSession] = None
    try:
        db_session = await anext(session_generator)
        if db_session is None:
            raise StopAsyncIteration

        for user_conf_data in SYSTEM_USERS_DATA:
            await create_system_user_if_not_exists(db_session, user_conf_data)

    except StopAsyncIteration:
        logger.error(_("Не вдалося отримати сесію бази даних для створення системних користувачів."))  # i18n
    except Exception as e:
        logger.error(_("Виникла непередбачена помилка під час виконання скрипта: {error}").format(error=e),
                     exc_info=True)  # i18n
    finally:
        if db_session is not None:
            try:
                await session_generator.aclose()
            except Exception as e:
                logger.error(_("Помилка при закритті сесії БД: {error}").format(error=e), exc_info=True)  # i18n

    # i18n: Log message - System users creation script finished
    logger.info(_("Завершено процес створення системних користувачів."))


def main():
    """
    Головна функція для запуску скрипта.
    """
    if sys.version_info >= (3, 7):
        asyncio.run(run_script_async_logic())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_script_async_logic())


if __name__ == "__main__":
    # Для запуску:
    # python backend/scripts/create_system_users.py
    #
    # Передумови:
    # 1. Змінна середовища DATABASE_URL має бути правильно налаштована.
    # 2. База даних має бути доступна, міграції застосовані.
    # 3. Довідники UserRole та UserType мають містити відповідні коди (SUPERUSER, ADMIN, BOT).
    # 4. Змінні середовища для паролів (ODIN_USER_PASSWORD, SHADOW_USER_PASSWORD, ROOT_USER_PASSWORD)
    #    можуть бути встановлені для використання визначених паролів. Якщо ні - будуть згенеровані випадкові.
    main()
