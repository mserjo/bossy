# backend/scripts/create_superuser.py
# -*- coding: utf-8 -*-
"""
Скрипт для створення суперкористувача системи.

Цей скрипт дозволяє створити нового користувача з правами суперкористувача,
вказавши email, пароль та інші дані через аргументи командного рядка
або через інтерактивні запити.
"""
import asyncio
import argparse
import os
import sys
import logging  # Стандартний модуль логування, який буде переналаштовано, якщо можливо
from getpass import getpass  # Для безпечного введення пароля
from typing import Optional  # Для типізації

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)
    # Це повідомлення може бути занадто раннім, якщо логер ще не налаштовано
    # print(f"DEBUG: Додано '{BACKEND_DIR}' до sys.path")

# --- Імпорт компонентів додатку ---
from sqlalchemy.ext.asyncio import AsyncSession

# Намагаємося імпортувати логер додатку. Якщо не вийде, використовуємо стандартний.
try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта create_superuser.") # i18n, додано уточнення
except ImportError:
    # Якщо логер додатку не доступний (наприклад, скрипт запускається у зовсім іншому середовищі),
    # налаштовуємо базовий логер для цього скрипта.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)  # Логер для цього модуля
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для скрипта create_superuser.") # i18n, додано уточнення

# Використовуємо get_db_session для отримання сесії в контексті скрипта
from backend.app.src.core.database import get_db_session
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.schemas.auth.user_schemas import UserCreateSuperuserSchema
from backend.app.src.models.auth import User as UserModel
from backend.app.src.repositories.auth.user_repository import UserRepository
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository
from backend.app.src.repositories.dictionaries.user_type_repository import UserTypeRepository
from backend.app.src.core.constants import UserRoleEnum, UserTypeEnum


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    # У реальному сценарії тут була б інтеграція з gettext або іншою i18n бібліотекою.
    return text


async def create_superuser_logic(db: AsyncSession, args: argparse.Namespace):
    """
    Асинхронна логіка для створення суперкористувача.

    Args:
        db: Асинхронна сесія бази даних.
        args: Аргументи командного рядка, що містять дані користувача.
    """
    user_repo = UserRepository(db_session=db)
    user_role_repo = UserRoleRepository(db_session=db)
    user_type_repo = UserTypeRepository(db_session=db)
    user_service = UserService(db_session=db)

    # i18n: Log message - Checking user existence by email
    logger.info(_("Перевірка існування користувача з email: {email}").format(email=args.email))
    existing_user_by_email: Optional[UserModel] = await user_repo.get_by_email(email=args.email)
    if existing_user_by_email:
        # i18n: Error message - User with email already exists
        logger.error(_("Помилка: Користувач з email '{email}' вже існує.").format(email=args.email))
        return

    if args.username:
        # i18n: Log message - Checking user existence by username
        logger.info(_("Перевірка існування користувача з нікнеймом: {username}").format(username=args.username))
        existing_user_by_username: Optional[UserModel] = await user_repo.get_by_username(username=args.username)
        if existing_user_by_username:
            # i18n: Error message - User with username already exists
            logger.error(_("Помилка: Користувач з нікнеймом '{username}' вже існує.").format(username=args.username))
            return

    # Отримання ID для ролі 'superuser' та типу 'superuser'
    try:
        superuser_role_code = UserRoleEnum.SUPERUSER.value
        superuser_type_code = UserTypeEnum.SUPERUSER.value
    except AttributeError:
        logger.error(
            _("Помилка: Не вдалося отримати значення для UserRoleEnum.SUPERUSER або UserTypeEnum.SUPERUSER. Перевірте константи `backend.app.src.core.constants`."))  # i18n
        return

    superuser_role = await user_role_repo.get_by_code(code=superuser_role_code)
    if not superuser_role:
        # i18n: Error message - Superuser role not found
        logger.error(
            _("Помилка: Роль '{role_code}' не знайдена в довіднику ролей.").format(role_code=superuser_role_code))
        logger.error(
            _("Будь ласка, спочатку заповніть довідники (наприклад, за допомогою `backend.scripts.run_seed` або відповідного сервісу ініціалізації)."))  # i18n
        return

    superuser_type = await user_type_repo.get_by_code(code=superuser_type_code)
    if not superuser_type:
        # i18n: Error message - Superuser type not found
        logger.error(_("Помилка: Тип користувача '{type_code}' не знайдений в довіднику типів.").format(
            type_code=superuser_type_code))
        logger.error(_("Будь ласка, спочатку заповніть довідники."))  # i18n
        return

    try:
        # Схема UserCreateSuperuserSchema валідує дані.
        # Пароль буде хешовано сервісом.
        # is_active та is_superuser встановлюються сервісом create_superuser.
        superuser_data = UserCreateSuperuserSchema(
            email=args.email,
            password=args.password,
            first_name=args.first_name,
            last_name=args.last_name,
            username=args.username if args.username else None,
            user_role_id=superuser_role.id,
            user_type_id=superuser_type.id,
            # Явно передаємо is_verified, якщо схема цього вимагає, або сервіс це обробляє.
            # Якщо суперюзер має бути верифікований за замовчуванням:
            is_verified=True
        )
    except Exception as pydantic_exc:  # Обробка можливих помилок валідації Pydantic
        logger.error(_("Помилка валідації даних для суперкористувача: {error}").format(error=pydantic_exc))  # i18n
        return

    # i18n: Log message - Creating superuser with email
    logger.info(_("Створення суперюзера з email: {email}").format(email=args.email))
    try:
        # Метод сервісу для створення суперюзера.
        new_superuser: UserModel = await user_service.create_superuser(user_data=superuser_data)

        if new_superuser:
            # i18n: Success message - Superuser created
            logger.info(_("Суперюзер '{email}' (ID: {user_id}) успішно створений.").format(email=new_superuser.email,
                                                                                           user_id=new_superuser.id))
        else:
            # i18n: Error message - Failed to create superuser (unexpected service result)
            logger.error(_("Не вдалося створити суперюзера: сервіс не повернув очікуваний результат."))
    except Exception as e:
        # i18n: Error message - Error during superuser creation
        logger.error(_("Помилка під час створення суперюзера: {error}").format(error=e), exc_info=True)


async def run_script_async_logic():
    """
    Асинхронна функція для запуску логіки скрипта з отриманням сесії БД.
    """
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(description=_("Скрипт для створення нового суперкористувача в системі."))
    # i18n: Argparse help for --email argument
    parser.add_argument("--email", type=str, required=True, help=_("Email суперюзера (обов'язково)."))
    # i18n: Argparse help for --password argument
    parser.add_argument("--password", type=str,
                        help=_("Пароль суперюзера. Якщо не вказано, буде запитано інтерактивно."))
    # i18n: Argparse help for --first-name argument
    parser.add_argument("--first-name", type=str, default="Super",
                        help=_("Ім'я суперюзера (за замовчуванням: 'Super')."))
    # i18n: Argparse help for --last-name argument
    parser.add_argument("--last-name", type=str, default="User",
                        help=_("Прізвище суперюзера (за замовчуванням: 'User')."))
    # i18n: Argparse help for --username argument
    parser.add_argument("--username", type=str, help=_("Нікнейм суперюзера (опціонально, має бути унікальним)."))

    args = parser.parse_args()

    if not args.password:
        try:
            # i18n: Prompt for superuser password
            password_prompt = _("Введіть пароль для суперюзера: ")
            password = getpass(password_prompt)
            if not password:  # Перевірка на порожній пароль
                logger.error(_("Пароль не може бути порожнім. Створення суперюзера скасовано."))  # i18n
                return
            # i18n: Prompt to confirm superuser password
            password_confirm_prompt = _("Повторіть пароль: ")
            password_confirm = getpass(password_confirm_prompt)
        except KeyboardInterrupt:
            logger.warning(_("\nВведення пароля перервано. Створення суперюзера скасовано."))  # i18n
            return
        except EOFError:  # Може виникнути, якщо stdin не є терміналом (наприклад, при пайпінгу)
            logger.error(
                _("Не вдалося прочитати пароль. Переконайтеся, що скрипт запускається в інтерактивному режимі або пароль передано через аргумент --password."))  # i18n
            return

        if password != password_confirm:
            # i18n: Error message - Passwords do not match
            logger.error(_("Паролі не співпадають. Створення суперюзера скасовано."))
            return
        args.password = password

    # Отримання асинхронної сесії бази даних
    # Використовуємо get_db_session як асинхронний генератор
    session_generator = get_db_session()
    db_session: Optional[AsyncSession] = None
    try:
        db_session = await anext(session_generator)  # Отримуємо сесію з генератора
        if db_session is None:
            raise StopAsyncIteration  # Якщо сесія None, це еквівалентно кінцю генератора
        await create_superuser_logic(db_session, args)
    except StopAsyncIteration:
        logger.error(_("Не вдалося отримати сесію бази даних. Перевірте налаштування БД."))  # i18n
    except Exception as e:
        logger.error(_("Виникла непередбачена помилка під час роботи з сесією БД: {error}").format(error=e),
                     exc_info=True)  # i18n
    finally:
        if db_session is not None:
            # Важливо коректно закрити генератор сесій / саму сесію
            try:
                await session_generator.aclose()  # Закриваємо генератор (і сесію, якщо він так реалізований)
            except Exception as e:
                logger.error(_("Помилка при закритті сесії БД: {error}").format(error=e), exc_info=True)  # i18n


def main():
    """
    Головна функція для запуску скрипта.
    Налаштовує асинхронний цикл та викликає run_script_async_logic.
    """
    # i18n: Log message - Starting superuser creation script
    logger.info(_("Запуск скрипта створення суперкористувача..."))

    if sys.version_info >= (3, 7):
        asyncio.run(run_script_async_logic())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_script_async_logic())

    # i18n: Log message - Superuser creation script finished
    logger.info(_("Роботу скрипта створення суперюзера завершено."))


if __name__ == "__main__":
    # Приклад запуску:
    # python backend/scripts/create_superuser.py --email admin@example.com
    #
    # Передумови:
    # 1. Змінна середовища DATABASE_URL має бути правильно налаштована (див. backend/app/src/core/settings.py).
    # 2. База даних має бути доступна та міграції застосовані.
    # 3. Довідники UserRole та UserType мають містити записи для 'SUPERUSER'
    #    (зазвичай створюються скриптом `backend.scripts.run_seed` або сервісом ініціалізації).
    main()
