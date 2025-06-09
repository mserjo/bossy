# backend/scripts/create_superuser.py
import asyncio
import argparse
import os
import sys
import logging
from getpass import getpass # Для безпечного введення пароля

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session_context # Використовуємо контекстний менеджер для сесії
from app.src.services.auth.user import UserService
from app.src.schemas.auth.user import UserCreateSuperuser # Схема для створення суперюзера
from app.src.models.auth import User # Для перевірки типу
from app.src.repositories.auth.user import UserRepository # Для перевірки існування
from app.src.repositories.dictionaries.user_role import UserRoleRepository # Для отримання ID ролі суперюзера
from app.src.repositories.dictionaries.user_type import UserTypeRepository # Для отримання ID типу суперюзера
from app.src.core.constants import UserRoleEnum, UserTypeEnum # Припускаємо, що є такі Enum

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def create_superuser_logic(db: AsyncSession, args: argparse.Namespace):
    """
    Асинхронна логіка створення суперюзера.
    """
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)
    user_type_repo = UserTypeRepository(db)
    user_service = UserService(db) # UserService тепер приймає db напряму

    logger.info(f"Перевірка існування користувача з email: {args.email}")
    existing_user = await user_repo.get_by_email(args.email)
    if existing_user:
        logger.error(f"Помилка: Користувач з email '{args.email}' вже існує.")
        return

    if args.username:
        logger.info(f"Перевірка існування користувача з нікнеймом: {args.username}")
        existing_username = await user_repo.get_by_username(args.username)
        if existing_username:
            logger.error(f"Помилка: Користувач з нікнеймом '{args.username}' вже існує.")
            return

    # Отримання ID ролі 'superuser' та типу 'superuser'
    # Припускаємо, що коди 'SUPERUSER' є в довідниках UserRole та UserType
    superuser_role_value = UserRoleEnum.SUPERUSER.value if isinstance(UserRoleEnum.SUPERUSER, UserRoleEnum) else UserRoleEnum.SUPERUSER
    superuser_type_value = UserTypeEnum.SUPERUSER.value if isinstance(UserTypeEnum.SUPERUSER, UserTypeEnum) else UserTypeEnum.SUPERUSER

    superuser_role = await user_role_repo.get_by_code(superuser_role_value)
    if not superuser_role:
        logger.error(f"Помилка: Роль '{superuser_role_value}' не знайдена в довіднику ролей.")
        logger.error("Будь ласка, спочатку заповніть довідники (наприклад, за допомогою run_seed.py).")
        return

    superuser_type = await user_type_repo.get_by_code(superuser_type_value)
    if not superuser_type:
        logger.error(f"Помилка: Тип користувача '{superuser_type_value}' не знайдений в довіднику типів.")
        logger.error("Будь ласка, спочатку заповніть довідники.")
        return

    superuser_data = UserCreateSuperuser(
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name,
        username=args.username if args.username else None, # Передаємо None, якщо username не вказано
        user_role_id=superuser_role.id,
        user_type_id=superuser_type.id,
        is_active=True,      # Суперюзер активний за замовчуванням
        is_superuser=True    # Явно вказуємо, що це суперюзер
    )

    logger.info(f"Створення суперюзера з email: {args.email}")
    try:
        # UserService.create_user_by_superuser очікує UserCreateSuperuser
        # і сам встановлює is_superuser=True, is_active=True, хешує пароль.
        # Він також може перевіряти user_role_id та user_type_id.
        new_superuser = await user_service.create_user_by_superuser(user_create_schema=superuser_data)
        if isinstance(new_superuser, User):
            logger.info(f"Суперюзер '{new_superuser.email}' успішно створений.")
        else:
            # Це не повинно статися, якщо create_user_by_superuser працює правильно
            logger.error("Не вдалося створити суперюзера, сервіс повернув неочікуваний результат.")

    except Exception as e:
        logger.error(f"Помилка під час створення суперюзера: {e}", exc_info=True)

async def main_async():
    """
    Асинхронна обгортка для основної логіки.
    """
    parser = argparse.ArgumentParser(description="Створення нового суперюзера в системі.")
    parser.add_argument("--email", type=str, required=True, help="Email суперюзера (обов'язково)")
    parser.add_argument("--password", type=str, help="Пароль суперюзера. Якщо не вказано, буде запитано.")
    parser.add_argument("--first-name", type=str, default="Super", help="Ім'я суперюзера (за замовчуванням: Super)")
    parser.add_argument("--last-name", type=str, default="User", help="Прізвище суперюзера (за замовчуванням: User)")
    parser.add_argument("--username", type=str, help="Нікнейм суперюзера (опціонально, має бути унікальним)")

    args = parser.parse_args()

    if not args.password:
        password = getpass("Введіть пароль для суперюзера: ")
        password_confirm = getpass("Повторіть пароль: ")
        if password != password_confirm:
            logger.error("Паролі не співпадають. Створення суперюзера скасовано.")
            return
        args.password = password

    # Використання асинхронного контекстного менеджера для сесії
    async with get_db_session_context() as db_session:
        await create_superuser_logic(db_session, args)

def main():
    # Запуск асинхронної функції main_async
    # Перевірка версії Python для asyncio.run
    if sys.version_info >= (3, 7):
        asyncio.run(main_async())
    else:
        # Для старіших версій Python (до 3.7) може знадобитися інший підхід
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_async())

if __name__ == "__main__":
    # Для запуску: python backend/scripts/create_superuser.py --email admin@example.com
    # Переконайтеся, що DATABASE_URL правильно налаштований в .env
    # та доступний для `app.src.config.database`.
    # Також, довідники ролей та типів мають бути заповнені.
    main()
