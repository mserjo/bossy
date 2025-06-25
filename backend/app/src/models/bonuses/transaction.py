# backend/app/src/models/bonuses/transaction.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TransactionModel` для зберігання всіх транзакцій
по рахунках користувачів. Транзакції фіксують будь-які зміни балансу:
нарахування бонусів за завдання, списання за нагороди, штрафи, перекази тощо.
"""

from sqlalchemy import Column, ForeignKey, Numeric, Text, String, DateTime # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class TransactionModel(BaseModel):
    """
    Модель для транзакцій по рахунках користувачів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор транзакції (успадковано).
        account_id (uuid.UUID): Ідентифікатор рахунку, до якого відноситься транзакція.
                                Рахунок (`AccountModel`) вже містить `bonus_type_code`,
                                тому транзакція відбувається у валюті рахунку.
        amount (Numeric): Сума транзакції. Позитивна для нарахувань, від'ємна для списань.
        transaction_type_code (str): Код типу транзакції (наприклад, "TASK_COMPLETION", "REWARD_PURCHASE").
                                     Має посилатися на довідник або Enum.
        description (Text | None): Опис транзакції.

        source_entity_type (str | None): Тип сутності, що спричинила транзакцію ('task_completion', 'reward', 'user_transfer', 'system_adjustment').
        source_entity_id (uuid.UUID | None): ID сутності-джерела.

        related_user_id (uuid.UUID | None): ID пов'язаного користувача (наприклад, для "подяки" - кому подякували, або від кого).

        metadata (JSONB | None): Додаткові структуровані дані.
        balance_after_transaction (Numeric | None): Баланс рахунку після цієї транзакції.

        created_at (datetime): Дата та час створення транзакції (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, зазвичай не оновлюється).

    Зв'язки:
        account (relationship): Зв'язок з AccountModel.
        related_user (relationship): Зв'язок з UserModel (для transfer/thank_you).
    """
    __tablename__ = "transactions"

    account_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Column[Numeric] = Column(Numeric(12, 2), nullable=False)

    # Код типу транзакції.
    # TODO: Створити Enum або довідник для TransactionTypeType.
    # Приклади: "TASK_REWARD", "TASK_PENALTY", "REWARD_PURCHASE", "MANUAL_ADJUSTMENT_CREDIT",
    # "MANUAL_ADJUSTMENT_DEBIT", "THANK_YOU_SENT", "THANK_YOU_RECEIVED", "INITIAL_BALANCE".
    transaction_type_code: Column[str] = Column(String(100), nullable=False, index=True)

    description: Column[str | None] = Column(Text, nullable=True)

    # --- Інформація про джерело/причину транзакції ---
    # Тип сутності, що є джерелом. Наприклад, 'TaskCompletionModel', 'RewardModel', 'UserModel' (для переказу), 'SystemAdjustment'.
    # Це допоможе потім отримати деталі про джерело.
    source_entity_type: Column[str | None] = Column(String(100), nullable=True, index=True)
    source_entity_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), nullable=True, index=True)
    # TODO: Додати індекс на (source_entity_type, source_entity_id).

    # ID пов'язаного користувача, якщо транзакція є переказом або подякою.
    # Наприклад, якщо це 'THANK_YOU_SENT', то related_user_id - це той, кому відправили.
    # Якщо 'THANK_YOU_RECEIVED', то related_user_id - це той, від кого отримали.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    related_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_transactions_related_user_id", ondelete="SET NULL"), nullable=True, index=True)

    metadata: Column[JSONB | None] = Column(JSONB, nullable=True) # Для будь-яких додаткових даних

    balance_after_transaction: Column[Numeric | None] = Column(Numeric(12, 2), nullable=True) # Для аудиту

    # --- Зв'язки (Relationships) ---
    account = relationship("AccountModel", back_populates="transactions")
    related_user = relationship("UserModel", foreign_keys=[related_user_id]) # back_populates="related_transactions" буде в UserModel

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', account_id='{self.account_id}', amount='{self.amount}', type='{self.transaction_type_code}')>"

# Важливо: Валюта (тип бонусів) цієї транзакції визначається валютою рахунку (`AccountModel.bonus_type_code`),
# до якого вона прив'язана. Якщо `AccountModel.bonus_type_code` може змінюватися,
# і це не призводить до конвертації старих транзакцій або створення нового рахунку,
# тоді `TransactionModel` повинна зберігати `bonus_type_code` на момент транзакції.
# Поточна реалізація `AccountModel` (після моїх роздумів і повернення до версії з `bonus_type_code`)
# передбачає, що `AccountModel.bonus_type_code` фіксує валюту цього рахунку.
# Якщо група змінює тип валюти, то це складна операція, яка може включати:
# 1. Створення нових рахунків для користувачів з новим `bonus_type_code`.
# 2. Конвертацію балансів старих рахунків на нові (якщо можливо і потрібно).
# 3. "Замороження" старих рахунків.
# Або ж, простіше, група не може змінювати тип валюти після того, як по ній були транзакції.
# Припускаючи, що `AccountModel.bonus_type_code` є стабільним для даного рахунку,
# `TransactionModel` не потребує власного поля `bonus_type_code`.
# Це узгоджується зі структурою, де `AccountTransactionSchema` не має `bonus_type_code`.
#
# Поле `transaction_type_code` - це класифікатор самої операції (за що нараховано/списано).
# Поля `source_entity_type` та `source_entity_id` дозволяють зв'язати транзакцію
# з конкретним об'єктом, що її спричинив (наприклад, конкретне виконання завдання або куплена нагорода).
# `related_user_id` корисний для транзакцій типу "подяка" або переказів між користувачами (якщо будуть).
# `balance_after_transaction` - корисне для аудиту та швидкого відновлення історії балансу.
# `ondelete="CASCADE"` для `account_id` - логічно.
# `ondelete="SET NULL"` для `related_user_id` - якщо пов'язаний користувач видаляється, транзакція залишається,
# але зв'язок втрачається (стає "невідомим користувачем").
# Все виглядає узгоджено.
