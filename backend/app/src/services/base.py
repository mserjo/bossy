# backend/app/src/services/base.py
# import logging # Замінено на централізований логер
from typing import TypeVar, Generic, Optional, Any, Type  # Додано Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Додано для get_object_or_none

from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)

# Генеричний тип для моделей SQLAlchemy, якщо буде потрібно в майбутньому для більш типізованих методів
ModelType = TypeVar("ModelType")


# Генеричний тип для репозиторію, якщо використовується патерн "Репозиторій".
# Наразі не використовується активно в сервісах, але залишено для можливого розширення.
# from backend.app.src.repositories.base import BaseRepository # Приклад базового репозиторію
# RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)

class BaseService(Generic[ModelType]):  # Прибрано RepositoryType, оскільки не використовується
    """
    Базовий клас для всіх сервісів.
    Надає спільні функціональні можливості та залежності для класів сервісів,
    такі як сесія бази даних.

    Сервіси відповідають за інкапсуляцію бізнес-логіки та координацію
    доступу до даних через репозиторії (якщо використовується патерн "Репозиторій")
    або безпосередньо через ORM/сесії бази даних.

    Атрибути:
        db_session (AsyncSession): Асинхронна сесія бази даних SQLAlchemy.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує BaseService з сесією бази даних.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy,
                           яка буде використовуватися для операцій з базою даних.
        :raises ValueError: Якщо db_session не надано (None).
        """
        if db_session is None:
            # Ця перевірка є критично важливою. Сервіси не повинні працювати без сесії БД.
            # i18n
            msg = "Сесія бази даних не може бути None для BaseService."
            logger.error(f"BaseService ініціалізовано без сесії бази даних. {msg}")
            raise ValueError(msg)

        self.db_session: AsyncSession = db_session

        logger.debug(
            f"{self.__class__.__name__} ініціалізовано з ID сесії БД: {id(db_session)}"
        )

    async def commit(self) -> None:
        """
        Здійснює коміт поточної сесії бази даних.
        Логує дію та обробляє потенційні винятки під час коміту.
        У разі помилки коміту, намагається виконати відкат.
        """
        try:
            await self.db_session.commit()
            logger.info(f"Сесію бази даних {id(self.db_session)} успішно закомічено класом {self.__class__.__name__}.")
        except Exception as e:
            logger.error(f"Помилка коміту сесії бази даних {id(self.db_session)} в {self.__class__.__name__}: {e}",
                         exc_info=settings.DEBUG)
            # Залежно від стратегії обробки помилок, тут можна або відкотити, або передати виняток далі.
            # Наразі логуємо, намагаємося відкотити та передаємо виняток далі.
            await self.rollback()
            raise

    async def rollback(self) -> None:
        """
        Здійснює відкат поточної сесії бази даних.
        Логує дію та обробляє потенційні винятки під час відкату.
        """
        try:
            await self.db_session.rollback()
            logger.warning(f"Сесію бази даних {id(self.db_session)} відкочено класом {self.__class__.__name__}.")
        except Exception as e:
            logger.error(f"Помилка відкату сесії бази даних {id(self.db_session)} в {self.__class__.__name__}: {e}",
                         exc_info=settings.DEBUG)
            # Якщо відкат не вдався, сесія може бути в неузгодженому стані.
            # Це критична помилка.
            raise

    async def get_object_or_none(self, model_cls: Type[ModelType], object_id: UUID) -> Optional[ModelType]:
        """
        Допоміжний метод: отримує об'єкт за його ID, повертає None, якщо не знайдено.
        Використовує self.db_session для прямого запиту через SQLAlchemy.

        :param model_cls: Клас моделі SQLAlchemy для запиту.
        :param object_id: UUID об'єкта для пошуку.
        :return: Екземпляр моделі або None.
        """
        logger.debug(f"Спроба отримання {model_cls.__name__} з ID: {object_id}")

        # Припускаємо, що модель має атрибут 'id'
        if not hasattr(model_cls, 'id'):
            logger.error(f"Модель {model_cls.__name__} не має атрибута 'id'. Неможливо виконати get_object_or_none.")
            return None  # Або кинути AttributeError

        stmt = select(model_cls).where(getattr(model_cls, 'id') == object_id)
        result = await self.db_session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance:
            logger.debug(f"Знайдено {model_cls.__name__} з ID: {object_id}")
        else:
            logger.debug(f"{model_cls.__name__} з ID: {object_id} не знайдено.")
        return instance


logger.info("BaseService (базовий клас сервісів) успішно визначено.")
