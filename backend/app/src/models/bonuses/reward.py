# backend/app/src/models/bonuses/reward.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `RewardModel` для представлення нагород,
які користувачі можуть "купувати" або отримувати за накопичені бонуси.
Нагороди належать до певної групи та налаштовуються адміністратором групи.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, Numeric # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки нагорода має назву, опис, статус (доступна/недоступна),
# і належить до групи.
from backend.app.src.models.base import BaseMainModel

class RewardModel(BaseMainModel):
    """
    Модель для представлення нагород.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор нагороди (успадковано).
        name (str): Назва нагороди (наприклад, "Чашка кави", "Додатковий вихідний") (успадковано).
        description (str | None): Детальний опис нагороди (успадковано).
        state_id (uuid.UUID | None): Статус нагороди (наприклад, "доступна", "недоступна", "архівована").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, в якій доступна ця нагорода. (успадковано, тут буде NOT NULL)

        cost_points (Numeric): Вартість нагороди в бонусних балах.
        bonus_type_code (str): Код типу бонусів, в яких вимірюється вартість (з BonusTypeModel.code).
                               Це має відповідати типу бонусів, що використовуються в групі.

        quantity_available (int | None): Доступна кількість нагород (якщо обмежена).
                                          NULL означає необмежену кількість.
        max_per_user (int | None): Максимальна кількість, яку один користувач може отримати.
                                    NULL означає без обмежень.

        is_recurring_purchase (bool): Чи можна купувати цю нагороду повторно.

        # Поля для візуального представлення
        icon_file_id (uuid.UUID | None): Ідентифікатор файлу іконки нагороди (посилання на FileModel).

        # Поля для активації/використання нагороди (якщо це не просто списання балів)
        # activation_details (Text | None): Інструкції або деталі щодо активації/отримання нагороди.
        # requires_manual_fulfillment (bool): Чи потребує нагорода ручного виконання/видачі адміном.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        status (relationship): Зв'язок зі статусом нагороди (вже є через state_id з BaseMainModel).
        # icon_file (relationship): Зв'язок з FileModel.
        # purchases (relationship): Список покупок/отримань цієї нагороди (може бути реалізовано через TransactionModel).
        # bonus_type (relationship): Зв'язок з BonusTypeModel.
    """
    __tablename__ = "rewards"

    # group_id успадковано і має бути NOT NULL.
    # ForeignKey("groups.id") вже є в BaseMainModel.

    cost_points: Column[Numeric] = Column(Numeric(12, 2), nullable=False)

    # Код типу бонусів, в яких вказана вартість. Має відповідати типу бонусів групи.
    # TODO: Замінити "bonus_types.code" на константу або імпорт моделі BonusTypeModel.
    # Або, якщо вартість завжди у валюті групи, то це поле може бути непотрібним,
    # а тип валюти береться з налаштувань групи.
    # Проте, якщо нагорода може бути глобальною, а потім додаватися до груп,
    # то вказання типу валюти тут має сенс.
    # ТЗ: "належить до якоїсь групи", "можна обрати нагороду з доступного списку (і обміняти на бонуси на своєму рахунку)".
    # Це означає, що вартість має бути в валюті рахунку користувача, тобто валюті групи.
    # Тому `bonus_type_code` тут, ймовірно, денормалізація або має відповідати `AccountModel.bonus_type_code`.
    # Залишаю його, припускаючи, що він фіксує, в якій валюті ця вартість.
    bonus_type_code: Column[str] = Column(String(50), nullable=False, index=True)
    # TODO: Додати ForeignKey до `bonus_types.code` або `bonus_types.id`.

    quantity_available: Column[int | None] = Column(Integer, nullable=True) # NULL = нескінченно
    max_per_user: Column[int | None] = Column(Integer, nullable=True) # NULL = без обмежень

    is_recurring_purchase: Column[bool] = Column(Boolean, default=True, nullable=False) # Чи можна купувати багато разів

    # Іконка нагороди
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel.
    icon_file_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_rewards_icon_file_id"), nullable=True)

    # --- Зв'язки (Relationships) ---
    # group успадковано з BaseMainModel.
    # group = relationship("GroupModel", foreign_keys=[group_id], back_populates="rewards")
    # Потрібно переконатися, що foreign_keys=[group_id] не конфліктує.
    group = relationship("GroupModel", foreign_keys="RewardModel.group_id", back_populates="rewards")

    # icon_file = relationship("FileModel", foreign_keys=[icon_file_id]) # back_populates="reward_icon_for" буде в FileModel

    # Зв'язок з BonusTypeModel, щоб знати деталі про валюту.
    # bonus_type = relationship("BonusTypeModel",
    #                           primaryjoin="foreign(RewardModel.bonus_type_code) == remote(BonusTypeModel.code)",
    #                           uselist=False)
    # TODO: Реалізувати зв'язок з BonusTypeModel, якщо bonus_type_code використовується як ключ.
    # Або якщо буде bonus_type_id.

    # `state_id` з BaseMainModel використовується для статусу нагороди.
    # state = relationship("StatusModel", foreign_keys=[state_id])

    # Зв'язок з транзакціями, де ця нагорода була куплена (якщо source_entity_id в TransactionModel посилається сюди)
    # purchases = relationship(
    #     "TransactionModel",
    #     primaryjoin="and_(TransactionModel.source_entity_type == 'reward', foreign(TransactionModel.source_entity_id) == RewardModel.id)",
    #     lazy="dynamic" # Для можливості подальшої фільтрації
    # )
    # TODO: Визначити, чи потрібен такий явний зв'язок, чи достатньо фільтрувати транзакції.


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі RewardModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "належить до якоїсь групи" - `group_id`.
# - "(адмін групи) створення/редагування/видалення/блокування" - стандартні CRUD та `state_id`.
# - "(всі ролі) можна обрати нагороду ... (і обміняти на бонуси на своєму рахунку)" - `cost_points`.
# - "нагороди можуть бути разові, обмеженої кількості та постійні"
#   - `quantity_available` для обмеженої кількості.
#   - `is_recurring_purchase` (або `max_per_user`) для разових/постійних для одного користувача.

# TODO: Узгодити назву таблиці `rewards` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи. `group_id` має бути NOT NULL.
# Ключові поля: `cost_points`, `bonus_type_code`.
# Додаткові поля для обмежень: `quantity_available`, `max_per_user`, `is_recurring_purchase`.
# Поле для іконки `icon_file_id`.
# Зв'язки визначені.
# `Numeric(12, 2)` для `cost_points`.
# `bonus_type_code` має бути узгоджений з валютою групи. Якщо в групі одна валюта,
# то `bonus_type_code` тут може бути денормалізацією або братися з налаштувань групи.
# Якщо нагороди можуть бути глобальними, а потім додаватися до груп з різними валютами,
# то це поле важливе. Але ТЗ каже "належить до якоїсь групи".
# Отже, `bonus_type_code` має відповідати `AccountModel.bonus_type_code` для рахунків цієї групи.
# Це поле фіксує, в якій валюті вказана вартість нагороди.
# Все виглядає логічно.
# Поле `name` з `BaseMainModel` - назва нагороди.
# `description`, `state_id`, `notes`, `deleted_at`, `is_deleted` - успадковані.
# `group_id` - успадковане, але тут має бути обов'язковим.
# Зв'язок `group` уточнено з `foreign_keys="RewardModel.group_id"`.
# Зв'язок з `FileModel` для іконки.
# Можливий зв'язок з `TransactionModel` для відстеження покупок.
# Зв'язок з `BonusTypeModel` для деталей валюти.
