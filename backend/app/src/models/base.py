# backend/app/src/models/base.py

"""
Цей модуль визначає базові класи моделей для програми.
- `Base` імпортується з `config.database` і є декларативною базою для всіх моделей.
- `BaseModel` надає загальні поля, такі як `id` та часові мітки.
- `BaseMainModel` розширює `BaseModel` додатковими загальними полями для основних бізнес-сутностей.
"""

import logging
from typing import Optional, TypeVar

from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import Integer

from backend.app.src.config.database import Base # Декларативна база з налаштувань SQLAlchemy
from backend.app.src.models.mixins import (
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    GroupAffiliationMixin,
    NotesMixin
)

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

# Загальний TypeVariable, який можна використовувати для моделей ORM у сервісах/репозиторіях
ModelT = TypeVar("ModelT", bound="BaseModel")

class BaseModel(Base, TimestampedMixin):
    """
    Базовий клас для всіх моделей SQLAlchemy у програмі.
    Успадковує від глобального `Base` (declarative_base()) та `TimestampedMixin`.

    Включає:
        - id: Первинний ключ, цілочисельний стовпець.
        - created_at: Часова мітка створення (з TimestampedMixin).
        - updated_at: Часова мітка останнього оновлення (з TimestampedMixin).
    """
    __abstract__ = True  # Вказує, що цей клас не повинен зіставлятися з таблицею бази даних сам по собі

    @declared_attr
    def __tablename__(cls) -> str:
        # Автоматично генерувати назву таблиці з назви класу (наприклад, UserProfile -> user_profiles)
        # Це поширена конвенція, але її можна перевизначити в підкласах, якщо потрібно.
        import re
        name_parts = re.findall(r'[A-Z][^A-Z]*', cls.__name__)
        # Обробка випадку, коли назва класу може бути повністю у верхньому регістрі, наприклад "URLShortener" -> "url_shorteners"
        if not name_parts: # Якщо назва класу повністю у верхньому регістрі або одне слово
            return cls.__name__.lower() + "s"
        return "_".join(part.lower() for part in name_parts) + "s" # Просте утворення множини додаванням 's'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису")

class BaseMainModel(BaseModel, NameDescriptionMixin, StateMixin, SoftDeleteMixin, NotesMixin):
    """
    Базовий клас для основних бізнес-сутностей у програмі.
    Успадковує від `BaseModel` та включає інші загальні міксини.

    Включає (на додаток до полів BaseModel):
        - name: Назва сутності (з NameDescriptionMixin).
        - description: Опціональний детальний опис (з NameDescriptionMixin).
        - state: Поточний стан або статус (зі StateMixin).
        - deleted_at: Часова мітка для м'якого видалення (з SoftDeleteMixin).
        - is_deleted: Гібридна властивість для статусу м'якого видалення (з SoftDeleteMixin).
        - notes: Внутрішні нотатки або загальні зауваження (з NotesMixin).

    `GroupAffiliationMixin` тут навмисно пропущено, щоб зробити цю базову модель
    більш загальнозастосовною. Моделі, які пов'язані з групами, можуть включати
    `GroupAffiliationMixin` явно.
    Альтернативно, можна створити інший базовий клас, наприклад `BaseGroupAffiliatedMainModel`.
    """
    __abstract__ = True

    # Тут безпосередньо не визначено додаткових полів, вони надходять з успадкованих міксинів.
    # Специфічні моделі, що успадковують від цього, додаватимуть власні унікальні поля та зв'язки.

# Приклад більш специфічної базової моделі, яка включає приналежність до групи
class BaseGroupAffiliatedMainModel(BaseMainModel, GroupAffiliationMixin):
    """
    Базовий клас для основних бізнес-сутностей, які безпосередньо пов'язані з групою.
    Успадковує від `BaseMainModel` та додає `GroupAffiliationMixin`.
    """
    __abstract__ = True


if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури базової моделі.
    # Він не взаємодіє з базою даних безпосередньо тут.

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Базові моделі SQLAlchemy --- демонстрація структури")

    logger.info(f"BaseModel успадковує від: {BaseModel.__mro__}")
    logger.info(f"BaseMainModel успадковує від: {BaseMainModel.__mro__}")
    logger.info(f"BaseGroupAffiliatedMainModel успадковує від: {BaseGroupAffiliatedMainModel.__mro__}")

    # Показати згенеровані назви таблиць (концептуально)
    class User(BaseModel):
        __tablename__ = "users" # Явно встановлено для цього поширеного випадку
        username: Mapped[str]

    class ProductOffering(BaseModel):
        # Назва таблиці буде 'product_offerings' за замовчуванням
        pass

    class URLShortener(BaseModel):
        # Назва таблиці буде 'url_shorteners' за замовчуванням
        pass

    class SomeGroupedItem(BaseGroupAffiliatedMainModel):
        # Назва таблиці буде 'some_grouped_items' за замовчуванням
        # Матиме id, created_at, updated_at, name, description, state, deleted_at, notes, group_id
        specific_field: Mapped[Optional[str]]

    logger.debug(f"Приклад назви таблиці User (явно): {User.__tablename__}")
    logger.debug(f"Приклад назви таблиці ProductOffering (згенеровано): {ProductOffering.__tablename__}")
    logger.debug(f"Приклад назви таблиці URLShortener (згенеровано): {URLShortener.__tablename__}")
    logger.debug(f"Приклад назви таблиці SomeGroupedItem (згенеровано): {SomeGroupedItem.__tablename__}")

    # Щоб перевірити фактичні стовпці, вам потрібно було б ініціалізувати Base.metadata за допомогою engine
    # а потім отримати доступ до SomeGroupedItem.__table__.columns
    # Наприклад:
    # from sqlalchemy import create_engine
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це вимагало б визначення всіх таблиць, на які є посилання (наприклад, 'groups' для SomeGroupedItem).
    # logger.info(f"Стовпці в SomeGroupedItem: {[c.name for c in SomeGroupedItem.__table__.columns]}")

    logger.info("BaseModel надає 'id', 'created_at', 'updated_at'.")
    logger.info("BaseMainModel додає 'name', 'description', 'state', 'deleted_at', 'is_deleted' (гібрид), 'notes'.")
    logger.info("BaseGroupAffiliatedMainModel далі додає 'group_id'.")
