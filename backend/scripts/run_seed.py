# backend/scripts/run_seed.py
import asyncio
import os
import sys
import logging
from typing import List, Dict, Type, Any # Додано для типізації

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel # Для типізації schema_class

from app.src.core.dependencies import get_db_session_context
# Припускаємо, що існують сервіси або репозиторії для кожного довідника
from app.src.services.dictionaries.user_role import UserRoleService
from app.src.schemas.dictionaries.user_role import UserRoleCreate
from app.src.services.dictionaries.user_type import UserTypeService
from app.src.schemas.dictionaries.user_type import UserTypeCreate
from app.src.services.dictionaries.group_type import GroupTypeService
from app.src.schemas.dictionaries.group_type import GroupTypeCreate
from app.src.services.dictionaries.task_type import TaskTypeService
from app.src.schemas.dictionaries.task_type import TaskTypeCreate
from app.src.services.dictionaries.bonus_type import BonusTypeService
from app.src.schemas.dictionaries.bonus_type import BonusTypeCreate
# Додайте інші сервіси та схеми для довідників за потреби (статуси, календарі, месенджери)
from app.src.services.dictionaries.status import StatusService # Приклад для статусів
from app.src.schemas.dictionaries.status import StatusCreate # Приклад для статусів

from app.src.core.constants import ( # Припускаємо, що константи для кодів і назв є тут
    UserRoleEnum, UserTypeEnum, GroupTypeEnum, TaskTypeEnum, BonusTypeEnum, StatusEnum
)

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Дані для заповнення довідників ---
# Згідно з technical_task.txt
SEED_DATA: Dict[str, List[Dict[str, Any]]] = {
    "user_roles": [
        {"code": UserRoleEnum.SUPERUSER.value if hasattr(UserRoleEnum.SUPERUSER, 'value') else UserRoleEnum.SUPERUSER, "name": "Суперюзер", "description": "Повний доступ до всієї системи"},
        {"code": UserRoleEnum.ADMIN.value if hasattr(UserRoleEnum.ADMIN, 'value') else UserRoleEnum.ADMIN, "name": "Адміністратор групи", "description": "Керування в межах своєї групи"},
        {"code": UserRoleEnum.USER.value if hasattr(UserRoleEnum.USER, 'value') else UserRoleEnum.USER, "name": "Користувач групи", "description": "Звичайний користувач в групі"},
    ],
    "user_types": [
        {"code": UserTypeEnum.SUPERUSER.value if hasattr(UserTypeEnum.SUPERUSER, 'value') else UserTypeEnum.SUPERUSER, "name": "Суперюзер системи", "description": "Адміністратор найвищого рівня"},
        {"code": UserTypeEnum.ADMIN.value if hasattr(UserTypeEnum.ADMIN, 'value') else UserTypeEnum.ADMIN, "name": "Адміністратор (тип)", "description": "Тип для адміністраторів груп"},
        {"code": UserTypeEnum.USER.value if hasattr(UserTypeEnum.USER, 'value') else UserTypeEnum.USER, "name": "Користувач системи", "description": "Стандартний користувач системи"},
        {"code": UserTypeEnum.BOT.value if hasattr(UserTypeEnum.BOT, 'value') else UserTypeEnum.BOT, "name": "Системний бот", "description": "Автоматизований системний аккаунт"},
    ],
    "group_types": [
        {"code": GroupTypeEnum.FAMILY.value if hasattr(GroupTypeEnum.FAMILY, 'value') else GroupTypeEnum.FAMILY, "name": "Сім'я", "description": "Група для сімейного використання"},
        {"code": GroupTypeEnum.DEPARTMENT.value if hasattr(GroupTypeEnum.DEPARTMENT, 'value') else GroupTypeEnum.DEPARTMENT, "name": "Відділ", "description": "Група для робочого відділу"},
        {"code": GroupTypeEnum.ORGANIZATION.value if hasattr(GroupTypeEnum.ORGANIZATION, 'value') else GroupTypeEnum.ORGANIZATION, "name": "Організація", "description": "Група для цілої організації"},
    ],
    "task_types": [
        {"code": TaskTypeEnum.REGULAR.value if hasattr(TaskTypeEnum.REGULAR, 'value') else TaskTypeEnum.REGULAR, "name": "Звичайне завдання", "description": "Стандартне завдання"},
        {"code": TaskTypeEnum.COMPLEX.value if hasattr(TaskTypeEnum.COMPLEX, 'value') else TaskTypeEnum.COMPLEX, "name": "Складне завдання", "description": "Завдання підвищеної складності"},
    ],
    "bonus_types": [
        {"code": BonusTypeEnum.STANDARD.value if hasattr(BonusTypeEnum.STANDARD, 'value') else BonusTypeEnum.STANDARD, "name": "Стандартний бонус", "description": "Звичайний тип бонусу"},
        {"code": BonusTypeEnum.PENALTY.value if hasattr(BonusTypeEnum.PENALTY, 'value') else BonusTypeEnum.PENALTY, "name": "Штраф", "description": "Тип для штрафних балів"},
        {"code": BonusTypeEnum.REWARD.value if hasattr(BonusTypeEnum.REWARD, 'value') else BonusTypeEnum.REWARD, "name": "Нагорода", "description": "Тип для бонусів-нагород"},
    ],
    "statuses": [
        {"code": StatusEnum.ACTIVE.value if hasattr(StatusEnum.ACTIVE, 'value') else StatusEnum.ACTIVE, "name": "Активний", "description": "Запис активний"},
        {"code": StatusEnum.INACTIVE.value if hasattr(StatusEnum.INACTIVE, 'value') else StatusEnum.INACTIVE, "name": "Неактивний", "description": "Запис неактивний"},
        {"code": StatusEnum.PENDING.value if hasattr(StatusEnum.PENDING, 'value') else StatusEnum.PENDING, "name": "В очікуванні", "description": "Запис очікує дії"},
        {"code": StatusEnum.COMPLETED.value if hasattr(StatusEnum.COMPLETED, 'value') else StatusEnum.COMPLETED, "name": "Завершено", "description": "Запис завершено"},
        {"code": StatusEnum.ARCHIVED.value if hasattr(StatusEnum.ARCHIVED, 'value') else StatusEnum.ARCHIVED, "name": "Архівовано", "description": "Запис архівовано"},
    ]
}

async def seed_dictionary(db: AsyncSession, service_class: Type[Any], schema_class: Type[PydanticBaseModel], data_list: List[Dict[str, Any]], dict_name: str):
    """
    Загальна функція для заповнення одного довідника.
    """
    service = service_class(db)
    logger.info(f"Заповнення довідника: {dict_name}...")
    for item_data in data_list:
        # Перевіряємо, чи існує запис з таким кодом
        # Більшість сервісів довідників повинні мати метод get_by_code в своєму репозиторії
        if not hasattr(service, 'repo') or not hasattr(service.repo, 'get_by_code'):
            logger.error(f"Сервіс для '{dict_name}' не має репозиторію з методом 'get_by_code'. Пропускаємо.")
            return

        existing_item = await service.repo.get_by_code(code=item_data['code'])
        if existing_item:
            logger.info(f"Запис '{item_data['code']}' в довіднику '{dict_name}' вже існує. Пропускаємо.")
        else:
            try:
                schema_instance = schema_class(**item_data)
                # Більшість сервісів довідників повинні мати метод create
                if not hasattr(service, 'create'):
                     logger.error(f"Сервіс для '{dict_name}' не має методу 'create'. Пропускаємо створення запису '{item_data['code']}'.")
                     continue
                await service.create(create_schema=schema_instance)
                logger.info(f"Додано запис '{item_data['code']}' в довідник '{dict_name}'.")
            except Exception as e:
                logger.error(f"Помилка при додаванні запису '{item_data['code']}' в '{dict_name}': {e}", exc_info=True)
    logger.info(f"Завершено заповнення довідника: {dict_name}.")

async def main_async():
    """
    Асинхронна головна функція для заповнення всіх довідників.
    """
    logger.info("Запуск скрипта заповнення початкових даних (seed)...")

    async with get_db_session_context() as db_session:
        # Заповнення ролей користувачів
        await seed_dictionary(db_session, UserRoleService, UserRoleCreate, SEED_DATA["user_roles"], "Ролі користувачів")

        # Заповнення типів користувачів
        await seed_dictionary(db_session, UserTypeService, UserTypeCreate, SEED_DATA["user_types"], "Типи користувачів")

        # Заповнення типів груп
        await seed_dictionary(db_session, GroupTypeService, GroupTypeCreate, SEED_DATA["group_types"], "Типи груп")

        # Заповнення типів завдань
        if SEED_DATA["task_types"]:
             await seed_dictionary(db_session, TaskTypeService, TaskTypeCreate, SEED_DATA["task_types"], "Типи завдань")
        else:
            logger.info("Дані для довідника 'Типи завдань' відсутні, пропускаємо.")

        # Заповнення типів бонусів
        await seed_dictionary(db_session, BonusTypeService, BonusTypeCreate, SEED_DATA["bonus_types"], "Типи бонусів")

        # Заповнення статусів (приклад)
        await seed_dictionary(db_session, StatusService, StatusCreate, SEED_DATA["statuses"], "Статуси")

        # Додайте сюди заповнення інших довідників (календарі, месенджери), якщо потрібно

    logger.info("Завершено заповнення початкових даних.")

def main():
    if sys.version_info >= (3, 7):
        asyncio.run(main_async())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_async())

if __name__ == "__main__":
    # Для запуску: python backend/scripts/run_seed.py
    # Переконайтеся, що DATABASE_URL правильно налаштований.
    main()
