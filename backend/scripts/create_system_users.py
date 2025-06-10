# backend/scripts/create_system_users.py
import asyncio
import os
import sys
import logging
import uuid # Для генерації випадкових паролів, якщо потрібно

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session_context
from app.src.services.auth.user import UserService
from app.src.schemas.auth.user import UserCreateSuperuser # Використовуємо цю схему для обох, оскільки вона найбільш повна
from app.src.models.auth import User # Для перевірки типу
from app.src.repositories.auth.user import UserRepository
from app.src.repositories.dictionaries.user_role import UserRoleRepository
from app.src.repositories.dictionaries.user_type import UserTypeRepository
from app.src.core.constants import UserRoleEnum, UserTypeEnum
# from app.src.config.settings import settings_app # Якщо паролі з .env

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Визначення системних користувачів
# Паролі: краще генерувати випадкові або брати з .env. Для прикладу, поки що можуть бути фіксовані або генеровані.
SYSTEM_USERS_DATA = [
    {
        "email": os.getenv("ODIN_USER_EMAIL", "odin@kudos.system"),
        "username": "odin",
        "password_env_var": "ODIN_USER_PASSWORD", # Для логування, якщо пароль з .env
        "first_name": "Odin",
        "last_name": "System",
        "role_code": UserRoleEnum.SUPERUSER.value if hasattr(UserRoleEnum.SUPERUSER, 'value') else UserRoleEnum.SUPERUSER,
        "type_code": UserTypeEnum.SUPERUSER.value if hasattr(UserTypeEnum.SUPERUSER, 'value') else UserTypeEnum.SUPERUSER,
        "is_superuser": True,
        "is_active": True
    },
    {
        "email": os.getenv("SHADOW_USER_EMAIL", "shadow@kudos.system"),
        "username": "shadow",
        "password_env_var": "SHADOW_USER_PASSWORD",
        "first_name": "Shadow",
        "last_name": "Bot",
        "role_code": UserRoleEnum.ADMIN.value if hasattr(UserRoleEnum.ADMIN, 'value') else UserRoleEnum.ADMIN, # 'admin' або спеціальна роль 'system_bot_admin'
        "type_code": UserTypeEnum.BOT.value if hasattr(UserTypeEnum.BOT, 'value') else UserTypeEnum.BOT,    # Тип 'bot'
        "is_superuser": False,
        "is_active": True
    },
    # Додатково згадувався 'root' в technical_task.txt, але його роль не зовсім ясна.
    # Якщо 'root' потрібен як ще один суперадмін, можна додати:
    # {
    #     "email": os.getenv("ROOT_USER_EMAIL", "root@kudos.system"),
    #     "username": "root",
    #     "password_env_var": "ROOT_USER_PASSWORD",
    #     "first_name": "Root",
    #     "last_name": "System",
    #     "role_code": UserRoleEnum.SUPERUSER.value if hasattr(UserRoleEnum.SUPERUSER, 'value') else UserRoleEnum.SUPERUSER,
    #     "type_code": UserTypeEnum.SUPERUSER.value if hasattr(UserTypeEnum.SUPERUSER, 'value') else UserTypeEnum.SUPERUSER,
    #     "is_superuser": True,
    #     "is_active": True
    # },
]

async def create_system_user_if_not_exists(db: AsyncSession, user_data_config: dict):
    """
    Створює системного користувача, якщо він ще не існує.
    """
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)
    user_type_repo = UserTypeRepository(db)
    user_service = UserService(db)

    email = user_data_config['email']
    username = user_data_config.get('username')

    # Отримуємо пароль з .env або генеруємо новий
    password = os.getenv(user_data_config["password_env_var"])
    generated_password_info = ""
    if not password:
        password = str(uuid.uuid4())
        generated_password_info = f"(ПАРОЛЬ ЗГЕНЕРОВАНО: {password} - ОБОВ'ЯЗКОВО ЗБЕРЕЖІТЬ ЙОГО!)"


    logger.info(f"Перевірка системного користувача: {email} (нік: {username})")
    existing_user = await user_repo.get_by_email(email)
    if existing_user:
        logger.info(f"Системний користувач {email} вже існує.")
        return

    if username:
        existing_username = await user_repo.get_by_username(username)
        if existing_username:
            logger.info(f"Системний користувач з нікнеймом {username} вже існує.")
            return

    user_role = await user_role_repo.get_by_code(user_data_config['role_code'])
    if not user_role:
        logger.error(f"Помилка: Роль '{user_data_config['role_code']}' не знайдена для користувача {email}.")
        logger.error("Будь ласка, спочатку заповніть довідники (наприклад, за допомогою run_seed.py).")
        return

    user_type = await user_type_repo.get_by_code(user_data_config['type_code'])
    if not user_type:
        logger.error(f"Помилка: Тип користувача '{user_data_config['type_code']}' не знайдений для {email}.")
        logger.error("Будь ласка, спочатку заповніть довідники.")
        return

    create_schema = UserCreateSuperuser(
        email=email,
        password=password,
        first_name=user_data_config.get('first_name'),
        last_name=user_data_config.get('last_name'),
        username=username,
        user_role_id=user_role.id,
        user_type_id=user_type.id,
        is_active=user_data_config.get('is_active', True),
        is_superuser=user_data_config.get('is_superuser', False)
        # notes: "Системний користувач, створений автоматично" # Можна додати нотатки
    )

    try:
        logger.info(f"Створення системного користувача: {create_schema.email} з роллю '{user_data_config['role_code']}' та типом '{user_data_config['type_code']}'...")

        # Припускаємо, що user_service.create_user_by_superuser може обробляти is_superuser=False
        # або є більш загальний метод, як create_user_with_specifics.
        # Якщо create_user_by_superuser строго для суперюзерів, потрібна умова:
        if create_schema.is_superuser:
            new_user = await user_service.create_user_by_superuser(user_create_schema=create_schema)
        else:
            # Потрібно переконатися, що UserCreateSuperuser сумісний з create_user,
            # або створити UserCreate схему з даних create_schema.
            # Для простоти, припустимо, що create_user_by_superuser може це обробити
            # або що ми можемо передати UserCreateSuperuser до більш загального методу.
            # В ідеалі, UserService мав би метод, що приймає UserCreateSuperuser і діє відповідно.
            # Тут ми викликаємо create_user_by_superuser, і він сам має обробити прапор is_superuser.
            new_user = await user_service.create_user_by_superuser(user_create_schema=create_schema)


        if isinstance(new_user, User):
            logger.info(f"Системний користувач '{new_user.email}' успішно створений. {generated_password_info}")
        else:
            logger.error(f"Не вдалося створити системного користувача {create_schema.email}.")

    except Exception as e:
        logger.error(f"Помилка під час створення системного користувача {create_schema.email}: {e}", exc_info=True)

async def main_async():
    """
    Асинхронна головна функція для створення всіх визначених системних користувачів.
    """
    logger.info("Запуск скрипта створення системних користувачів...")

    async with get_db_session_context() as db_session:
        for user_conf in SYSTEM_USERS_DATA:
            await create_system_user_if_not_exists(db_session, user_conf)
    logger.info("Завершено процес створення системних користувачів.")

def main():
    if sys.version_info >= (3, 7):
        asyncio.run(main_async())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_async())

if __name__ == "__main__":
    # Для запуску: python backend/scripts/create_system_users.py
    # Переконайтеся, що DATABASE_URL, а також ролі та типи користувачів в довідниках існують.
    # Паролі для ODIN_USER_PASSWORD та SHADOW_USER_PASSWORD можна задати в .env.
    # Якщо вони не задані, скрипт згенерує випадкові паролі та виведе їх в лог.
    main()
