# backend/app/src/schemas/groups/group.py
"""
Pydantic схеми для сутності "Група" (Group).

Цей модуль визначає схеми для:
- Базового представлення групи (`GroupBaseSchema`).
- Створення нової групи (`GroupCreateSchema`).
- Оновлення існуючої групи (`GroupUpdateSchema`).
- Представлення групи у відповідях API (`GroupSchema`).
- Деталізованого представлення групи (`GroupDetailSchema`), включаючи учасників та налаштування.
"""
from datetime import datetime
from typing import Optional, List, Any  # Any для тимчасових полів

from pydantic import Field, EmailStr  # EmailStr може знадобитися для UserPublicProfileSchema, якщо email там

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin, SoftDeleteSchemaMixin
# BaseMainSchema не імпортуємо напряму, якщо GroupBaseSchema визначає поля самостійно
# або якщо поля BaseMainSchema не повністю співпадають з тим, що потрібно для GroupBaseSchema.
# Поточний план для GroupBaseSchema визначає поля, схожі на BaseMainSchema, але без group_id.

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для owner та members
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

# from backend.app.src.schemas.dictionaries.group_types import GroupTypeSchema # Для group_type
# from backend.app.src.schemas.groups.settings import GroupSettingSchema # Для settings
# from backend.app.src.schemas.groups.membership import GroupMembershipSchema # Для members, якщо потрібна роль

GroupTypeSchema = Any  # Тимчасовий заповнювач
GroupSettingSchema = Any  # Тимчасовий заповнювач
GroupMembershipSchema = Any  # Тимчасовий заповнювач

# Максимальна довжина для поля 'name' може бути винесена в константи.
GROUP_NAME_MAX_LENGTH = 255


class GroupBaseSchema(BaseSchema):
    """
    Базова схема для полів групи.
    Включає поля, спільні для створення, оновлення та представлення групи.
    """
    name: str = Field(
        ...,  # Обов'язкове поле
        max_length=GROUP_NAME_MAX_LENGTH,
        description="Назва групи.",
        examples=["Команда маркетингу", "Сімейний бюджет"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис групи (необов'язково)."
    )
    # TODO: Валідувати group_type_code на основі існуючих кодів в довіднику GroupType
    #       Це можна зробити за допомогою pydantic.validator або на рівні сервісу.
    group_type_code: str = Field(
        description="Код типу групи з довідника `dict_group_types` (наприклад, 'FAMILY', 'DEPARTMENT')."
    )
    # TODO: Розглянути використання Enum GroupState з core.dicts, якщо стани груп фіксовані.
    state: Optional[str] = Field(
        None,
        max_length=50,
        description="Стан групи (наприклад, 'active', 'archived', 'private'). Необов'язково.",
        examples=["active"]
    )
    notes: Optional[str] = Field(
        None,
        description="Додаткові нотатки щодо групи (необов'язково)."
    )


class GroupCreateSchema(GroupBaseSchema):
    """
    Схема для створення нової групи.
    Успадковує базові поля групи. `owner_id` зазвичай встановлюється сервісом
    на основі поточного автентифікованого користувача.
    """
    owner_id: Optional[int] = Field(
        None,
        description="ID користувача, який створює та стає власником групи. Встановлюється сервісом."
    )
    # При створенні групи можна також передавати початкові налаштування,
    # але це може бути реалізовано і як окремий крок або значення за замовчуванням в моделі GroupSetting.


class GroupUpdateSchema(GroupBaseSchema):
    """
    Схема для оновлення існуючої групи.
    Всі поля, успадковані з `GroupBaseSchema`, стають опціональними.
    Дозволяє оновлювати власника групи.
    """
    name: Optional[str] = Field(None, max_length=GROUP_NAME_MAX_LENGTH, description="Нова назва групи.")
    description: Optional[str] = Field(None, description="Новий опис групи.")
    group_type_code: Optional[str] = Field(None, description="Новий код типу групи.")
    state: Optional[str] = Field(None, max_length=50, description="Новий стан групи.")
    notes: Optional[str] = Field(None, description="Нові нотатки щодо групи.")
    owner_id: Optional[int] = Field(None, description="Новий ID власника групи.")


class GroupSchema(GroupBaseSchema, IDSchemaMixin, TimestampedSchemaMixin, SoftDeleteSchemaMixin):
    """
    Схема для представлення даних групи у відповідях API.
    Включає `id`, часові мітки, `deleted_at` та розширену інформацію про власника та тип групи.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # name, description, group_type_code, state, notes успадковані з GroupBaseSchema.

    owner: Optional[UserPublicProfileSchema] = Field(None, description="Публічний профіль власника групи.")
    # TODO: Замінити Any на GroupTypeSchema, коли вона буде імпортована.
    group_type: Optional[GroupTypeSchema] = Field(None, description="Об'єкт типу групи.")

    members_count: Optional[int] = Field(None, description="Кількість учасників у групі (обчислюване поле).",
                                         examples=[10])
    # model_config успадковується з GroupBaseSchema -> BaseSchema (from_attributes=True)


class GroupDetailSchema(GroupSchema):
    """
    Схема для деталізованого представлення групи.
    Додає список учасників (або членства) та налаштування групи до базової схеми `GroupSchema`.
    """
    # TODO: Замінити List[UserPublicProfileSchema] на List[GroupMembershipSchema] для включення ролі користувача в групі.
    #       Або створити спеціальну схему MemberSchema, що включає профіль користувача та його роль.
    members: Optional[List[UserPublicProfileSchema]] = Field(default_factory=list,
                                                             description="Список публічних профілів учасників групи.")

    # TODO: Замінити Any на GroupSettingSchema, коли вона буде імпортована.
    settings: Optional[GroupSettingSchema] = Field(None, description="Налаштування групи.")


if __name__ == "__main__":
    # Демонстраційний блок для схем груп.
    logger.info("--- Pydantic Схеми для Груп (Group) ---")

    logger.info("\nGroupBaseSchema (приклад):")
    base_data = {
        "name": "Базова Група",  # TODO i18n
        "group_type_code": "DEPARTMENT",
        "description": "Опис базової групи."  # TODO i18n
    }
    base_instance = GroupBaseSchema(**base_data)
    logger.info(base_instance.model_dump_json(indent=2))

    logger.info("\nGroupCreateSchema (приклад):")
    create_data = {
        "name": "Нова Команда",  # TODO i18n
        "group_type_code": "TEAM_PROJECT",
        "description": "Команда для нового проекту X.",  # TODO i18n
        # owner_id не вказується клієнтом, а встановлюється сервером
    }
    create_instance = GroupCreateSchema(**create_data)
    logger.info(create_instance.model_dump_json(indent=2))

    logger.info("\nGroupUpdateSchema (приклад):")
    update_data = {"description": "Оновлений опис команди для проекту X.", "state": "archived"}  # TODO i18n
    update_instance = GroupUpdateSchema(**update_data)
    logger.info(update_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nGroupSchema (приклад відповіді API):")
    group_response_data = {
        "id": 1,
        "name": "Основна Група",  # TODO i18n
        "group_type_code": "GENERAL",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "owner": {"id": 101, "name": "Власник Групи"},  # TODO i18n (UserPublicProfileSchema)
        # "group_type": {"id": 1, "name": "Загальний", "code": "GENERAL"}, # Приклад GroupTypeSchema
        "members_count": 5
    }
    group_response_instance = GroupSchema(**group_response_data)
    logger.info(group_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nGroupDetailSchema (приклад деталізованої відповіді API):")
    group_detail_data = {
        **group_response_data,  # Успадковує поля з GroupSchema
        "members": [
            {"id": 101, "name": "Власник Групи"},  # TODO i18n
            {"id": 102, "name": "Учасник Один"}  # TODO i18n
        ],
        # "settings": {"currency_name": "бали", "allow_decimal_bonuses": False} # Приклад GroupSettingSchema
    }
    group_detail_instance = GroupDetailSchema(**group_detail_data)
    logger.info(group_detail_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми `GroupTypeSchema`, `GroupSettingSchema` та представлення учасників (`members`)")
    logger.info("наразі використовують заповнювачі (Any або базові типи). Їх потрібно буде замінити")
    logger.info("на відповідні конкретні схеми після їх рефакторингу/визначення.")
    logger.info("Також, `group_type_code` потребує валідації на рівні сервісу або схеми.")
