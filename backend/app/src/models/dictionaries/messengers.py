# backend/app/src/models/dictionaries/messengers.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для довідника "Месенджери" (платформи обміну повідомленнями).
Цей модуль визначає модель `MessengerPlatform`, яка представляє записи
в довіднику платформ месенджерів, з якими система може інтегруватися
для надсилання сповіщень (наприклад, Telegram, Viber, Slack).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionary
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import String

class MessengerPlatform(BaseDictionary):
    """
    Модель SQLAlchemy для довідника "Платформи месенджерів".

    Успадковує всі поля від `BaseDictionary` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для цього типу довідника, ймовірно, буде NULL, оскільки це системний довідник.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_messenger_platforms`).
        """
    __tablename__ = "dict_messenger_platforms"

    # Якщо для платформ месенджерів потрібні специфічні додаткові поля,
    # наприклад, деталі конфігурації API (які можуть бути зашифровані або зберігатися окремо),
    # їх можна визначити тут або в пов'язаній моделі налаштувань інтеграції.
    # Наприклад:
    # webhook_url_template: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="Шаблон URL для вебхука (якщо застосовно)")
    # supports_buttons: Mapped[bool] = mapped_column(Boolean, default=False, comment="Чи підтримує платформа інтерактивні кнопки")

    # _repr_fields успадковуються та збираються автоматично з BaseDictionary.
    # Немає додаткових специфічних полів для __repr__ на цьому рівні.
    _repr_fields: tuple[str, ...] = ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі MessengerPlatform.
    logger.info("--- Модель Довідника: MessengerPlatform ---")
    logger.info(f"Назва таблиці: {MessengerPlatform.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.extend(['webhook_url_template', 'supports_buttons'])
    for field in expected_fields:
        logger.info(f"  - {field}")
        # Приклад створення екземпляра (без взаємодії з БД)
        example_messenger = MessengerPlatform(
            id=1,
            name="Telegram",
            description="Платформа обміну повідомленнями Telegram для надсилання сповіщень.",
            code="TELEGRAM",
            state="active"
        )
        from backend.app.src.config.logging import get_logger
        logger = get_logger(__name__)

        # Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
        # from sqlalchemy.orm import Mapped, mapped_column
        # from sqlalchemy import String

        class MessengerPlatform(BaseDictionary):
            """
            Модель SQLAlchemy для довідника "Платформи месенджерів".

            Успадковує всі поля від `BaseDictionary` (включаючи `id`, `name`, `description`, `code`,
            часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
            `group_id` для цього типу довідника, ймовірно, буде NULL, оскільки це системний довідник.

            Атрибути:
                __tablename__ (str): Назва таблиці в базі даних (`dict_messenger_platforms`).
            """
            __tablename__ = "dict_messenger_platforms"

            # Якщо для платформ месенджерів потрібні специфічні додаткові поля,
            # наприклад, деталі конфігурації API (які можуть бути зашифровані або зберігатися окремо),
            # їх можна визначити тут або в пов'язаній моделі налаштувань інтеграції.
            # Наприклад:
            # webhook_url_template: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="Шаблон URL для вебхука (якщо застосовно)")
            # supports_buttons: Mapped[bool] = mapped_column(Boolean, default=False, comment="Чи підтримує платформа інтерактивні кнопки")

            # _repr_fields успадковуються та збираються автоматично з BaseDictionary.
            # Немає додаткових специфічних полів для __repr__ на цьому рівні.
            _repr_fields: tuple[str, ...] = ()


        if __name__ == "__main__":
            # Демонстраційний блок для моделі MessengerPlatform.
            logger.info("--- Модель Довідника: MessengerPlatform ---")
            logger.info(f"Назва таблиці: {MessengerPlatform.__tablename__}")
            logger.info("\nОчікувані поля (успадковані та власні):")
            expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                               'group_id', 'notes']
            # Якщо додано кастомні поля:
            # expected_fields.extend(['webhook_url_template', 'supports_buttons'])
            for field in expected_fields:
                logger.info(f"  - {field}")
                # Приклад створення екземпляра (без взаємодії з БД)
                example_messenger = MessengerPlatform(
                    id=1,
                    name="Telegram",
                    description="Платформа обміну повідомленнями Telegram для надсилання сповіщень.",
                    code="TELEGRAM",
                    state="active"
                )
                logger.info(f"\nПриклад екземпляра MessengerPlatform (без сесії):\n  {example_messenger}")
                # Очікуваний __repr__ (порядок може відрізнятися):
                # <MessengerPlatform(id=1, name='Telegram', code='TELEGRAM', state='active')>
    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")