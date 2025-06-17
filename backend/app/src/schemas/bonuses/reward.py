# backend/app/src/schemas/bonuses/reward.py
"""
Pydantic схеми для сутності "Нагорода" (Reward).

Цей модуль визначає схеми для:
- Базового представлення нагороди (`RewardBaseSchema`).
- Створення нової нагороди (`RewardCreateSchema`).
- Оновлення існуючої нагороди (`RewardUpdateSchema`).
- Представлення даних про нагороду у відповідях API (`RewardSchema`).
- Запиту на отримання нагороди користувачем (`RedeemRewardRequestSchema`).
"""
from datetime import datetime
from typing import Optional, Any  # Any для тимчасових полів
from decimal import Decimal

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin, BaseMainSchema
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

# BaseMainSchema не успадковується напряму RewardBaseSchema, бо group_id там опціональний,
# а для створення нагороди group_id зазвичай обов'язковий (або з контексту).
# RewardSchema успадкує BaseMainSchema.

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.groups.group import GroupSchema # Або GroupBriefSchema
GroupSchema = Any  # Тимчасовий заповнювач

REWARD_NAME_MAX_LENGTH = 255
REWARD_ICON_URL_MAX_LENGTH = 512


class RewardBaseSchema(BaseSchema):
    """
    Базова схема для полів нагороди, спільних для створення та оновлення.
    """
    name: str = Field(
        ...,
        max_length=REWARD_NAME_MAX_LENGTH,
        description="Назва нагороди.",
        examples=["Безкоштовна кава", "Сертифікат на знижку"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис нагороди."
    )
    # group_id тут не вказується, оскільки для Create він часто береться з URL або контексту,
    # а для Update не змінюється або змінюється окремим ендпоінтом.
    # RewardSchema отримає group_id з BaseMainSchema.

    cost: Decimal = Field(
        ...,
        ge=Decimal("0.00"),  # Вартість не може бути від'ємною
        description="\"Вартість\" нагороди в одиницях бонусів групи.",
        examples=[Decimal("50.00"), Decimal("1000.00")]
    )
    quantity_available: Optional[int] = Field(
        None,  # None означає необмежену кількість
        ge=0,  # Кількість не може бути від'ємною
        description="Доступна кількість екземплярів цієї нагороди (NULL для необмеженої)."
    )
    icon_url: Optional[str] = Field(
        None,
        max_length=REWARD_ICON_URL_MAX_LENGTH,
        description="URL або шлях до іконки нагороди.",
        examples=["https://example.com/icons/coffee_cup.png"]
    )
    # TODO: Розглянути використання Enum RewardState з core.dicts, якщо стани нагород фіксовані.
    state: Optional[str] = Field(
        None,  # Або default="active"
        max_length=50,
        description="Стан нагороди (наприклад, 'active', 'archived', 'out_of_stock').",
        examples=["active"]
    )
    notes: Optional[str] = Field(
        None,
        description="Додаткові нотатки щодо нагороди."
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class RewardCreateSchema(RewardBaseSchema):
    """
    Схема для створення нової нагороди.
    `group_id` має бути наданий (зазвичай з контексту URL або тіла запиту, якщо потрібно).
    """
    group_id: int = Field(description="Ідентифікатор групи, до якої належить ця нагорода.")
    # Успадковує всі поля від RewardBaseSchema.
    pass


class RewardUpdateSchema(RewardBaseSchema):
    """
    Схема для оновлення існуючої нагороди.
    Всі поля, успадковані з `RewardBaseSchema`, стають опціональними.
    `group_id` зазвичай не оновлюється для існуючої нагороди.
    """
    name: Optional[str] = Field(None, max_length=REWARD_NAME_MAX_LENGTH)
    description: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    quantity_available: Optional[int] = Field(None, ge=0)  # Можна встановити в 0, щоб позначити "немає в наявності"
    icon_url: Optional[str] = Field(None, max_length=REWARD_ICON_URL_MAX_LENGTH)
    state: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    # group_id зазвичай не змінюється при оновленні. Якщо це потрібно, його можна додати сюди.


class RewardResponseSchema(BaseMainSchema):  # Renamed, Успадковує id, name, description, state, notes, group_id, timestamps
    """
    Схема для представлення даних про нагороду у відповідях API.
    Успадковує більшість полів від `BaseMainSchema`.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Reward, що не входять до BaseMainSchema або потребують іншого представлення
    cost: Decimal = Field(description="Вартість нагороди в бонусах.")
    quantity_available: Optional[int] = Field(description="Доступна кількість (NULL для необмеженої).")
    icon_url: Optional[str] = Field(None, max_length=REWARD_ICON_URL_MAX_LENGTH, description="URL іконки нагороди.")

    # Пов'язані об'єкти (якщо потрібно)
    # group: Optional[GroupSchema] = Field(None, description="Інформація про групу, до якої належить нагорода.")
    # `group_id` вже є, `group` об'єкт можна додавати за потреби розширення.
    # Наразі `BaseMainSchema` не має поля `group`, лише `group_id`.
    # Якщо модель Reward має зв'язок `group`, то тут можна його відобразити.


class RedeemRewardRequestSchema(BaseSchema):
    """
    Схема запиту на отримання (покупку) нагороди користувачем.
    """
    reward_id: int = Field(description="Ідентифікатор нагороди, яку користувач хоче отримати.")
    # user_id зазвичай береться з поточного автентифікованого користувача (сервісом).
    # group_id також може бути отриманий з контексту, наприклад, якщо користувач діє в рамках активної групи.
    # Якщо потрібно явно, їх можна додати сюди.
    quantity: int = Field(default=1, gt=0,
                          description="Кількість екземплярів нагороди для отримання (за замовчуванням 1).")


if __name__ == "__main__":
    # Демонстраційний блок для схем нагород.
    logger.info("--- Pydantic Схеми для Нагород (Reward) ---")

    logger.info("\nRewardCreateSchema (приклад для створення):")
    create_reward_data = {
        "name": "Подарунковий сертифікат на 200 грн",  # TODO i18n
        "description": "Сертифікат на покупки в магазині-партнері.",  # TODO i18n
        "group_id": 1,
        "cost": Decimal("2000.00"),  # Вартість у бонусах
        "quantity_available": 100,
        "icon_url": "https://example.com/certs/cert200.png",
        "state": "active"
    }
    create_reward_instance = RewardCreateSchema(**create_reward_data)
    logger.info(create_reward_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nRewardUpdateSchema (приклад для оновлення):")
    update_reward_data = {
        "description": "Сертифікат на покупки в магазині-партнері 'СуперМаркет'.",  # TODO i18n
        "quantity_available": 50
    }
    update_reward_instance = RewardUpdateSchema(**update_reward_data)
    logger.info(update_reward_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nRewardSchema (приклад відповіді API):")
    reward_response_data = {
        "id": 1,
        "name": "Ексклюзивна Футболка",  # TODO i18n
        "description": "Футболка з унікальним дизайном Kudos.",  # TODO i18n
        "group_id": 1,  # Або може бути None, якщо нагорода глобальна
        "cost": Decimal("500.00"),
        "quantity_available": 25,
        "icon_url": "https://example.com/swag/kudos_tshirt.png",
        "state": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    reward_response_instance = RewardResponseSchema(**reward_response_data) # Renamed
    logger.info(reward_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nRedeemRewardRequestSchema (приклад запиту на отримання):")
    redeem_data = {"reward_id": 1, "quantity": 1}
    redeem_instance = RedeemRewardRequestSchema(**redeem_data)
    logger.info(redeem_instance.model_dump_json(indent=2))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних нагород.")
    logger.info("Поле 'state' для нагород може використовувати значення з довідника статусів або спеціального Enum.")
