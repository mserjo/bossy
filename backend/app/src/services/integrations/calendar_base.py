# backend/app/src/services/integrations/calendar_base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession # Для потенційної взаємодії з БД (токени/налаштування)

from backend.app.src.services.base import BaseService
from backend.app.src.models.auth.user import User # Для контексту користувача (не використовується прямо тут, але в підкласах)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

from pydantic import BaseModel, Field # Використовуємо Pydantic для структур даних

# TODO: Розглянути переміщення Pydantic моделей CalendarEventData та CalendarInfo
#  до відповідного файлу схем, наприклад, backend/app/src/schemas/integrations/calendar.py

class CalendarEventData(BaseModel):
    """
    Pydantic модель для уніфікованого представлення даних календарної події.
    """
    id: Optional[str] = Field(None, description="Унікальний ID події від провайдера") # i18n
    title: str = Field(..., description="Назва або короткий опис події") # i18n
    start_time: datetime = Field(..., description="Час початку події (з інформацією про часовий пояс)") # i18n
    end_time: datetime = Field(..., description="Час закінчення події (з інформацією про часовий пояс)") # i18n
    description: Optional[str] = Field(None, description="Детальний опис події") # i18n
    location: Optional[str] = Field(None, description="Місце проведення події") # i18n
    is_all_day: bool = Field(False, description="True, якщо подія триває весь день") # i18n
    attendees: Optional[List[str]] = Field(default_factory=list, description="Список email-адрес учасників") # i18n
    meeting_link: Optional[str] = Field(None, description="Посилання на онлайн-зустріч (наприклад, Google Meet, Teams)") # i18n
    # raw: Optional[Dict[str, Any]] = Field(None, description="Оригінальні необроблені дані події від провайдера") # Для відладки

class CalendarInfo(BaseModel):
    """
    Pydantic модель для інформації про календар користувача.
    """
    id: str = Field(..., description="Унікальний ID календаря від провайдера") # i18n
    name: str = Field(..., description="Відображуване ім'я календаря (наприклад, 'Основний', 'Робота')") # i18n
    is_primary: bool = Field(False, description="True, якщо це основний календар користувача на платформі") # i18n
    can_edit: bool = Field(False, description="True, якщо застосунок має права на запис до цього календаря") # i18n


class BaseCalendarIntegrationService(BaseService, ABC):
    """
    Абстрактний базовий клас для сервісів інтеграції з календарями.
    Визначає спільний інтерфейс для взаємодії з різними календарними платформами,
    такими як Google Calendar, Outlook Calendar тощо.

    Потребує конкретних реалізацій для кожного окремого провайдера календарів.
    Може потребувати зберігання OAuth токенів або API ключів, потенційно в моделі
    UserIntegrationCredential або подібній.
    """

    service_name: str # Має бути визначено в підкласах, наприклад, "GOOGLE_CALENDAR"

    def __init__(self, db_session: AsyncSession, user_id_for_context: Optional[int] = None): # Змінено UUID на int
        """
        Ініціалізує сервіс з сесією БД (для зберігання токенів/налаштувань через BaseService)
        та опціонально user_id, якщо операції специфічні для користувача.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param user_id_for_context: ID користувача для контексту операцій.
        """
        super().__init__(db_session) # BaseService надає self.db_session
        self.user_id_for_context = user_id_for_context # Для операцій, специфічних для користувача
        logger.info(f"BaseCalendarIntegrationService (підклас: {self.__class__.__name__}) ініціалізовано для користувача: {self.user_id_for_context or 'N/A'}.")

    @abstractmethod
    async def connect_account(self, auth_code: str, redirect_uri: str, user_id: int) -> Dict[str, Any]: # Змінено UUID на int
        """
        Підключає обліковий запис календаря користувача за допомогою коду авторизації (OAuth2).
        Повинен безпечно зберігати токени (наприклад, в БД, зашифровані).

        :param auth_code: Код авторизації, отриманий від провайдера OAuth.
        :param redirect_uri: URI перенаправлення, використаний в процесі OAuth.
        :param user_id: ID користувача, що підключає свій обліковий запис.
        :return: Словник зі статусом підключення та email/ID календаря користувача.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'connect_account' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def disconnect_account(self, user_id: int) -> bool: # Змінено UUID на int
        """
        Відключає обліковий запис календаря користувача, відкликаючи токени.
        Повинен видаляти збережені токени.

        :param user_id: ID користувача, чий обліковий запис відключається.
        :return: True, якщо відключення успішне, інакше False.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'disconnect_account' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def refresh_access_token_if_needed(self, user_id: int) -> bool: # Змінено UUID на int
        """
        Перевіряє, чи не закінчився термін дії access-токену для користувача,
        і оновлює його за допомогою refresh-токену. Оновлює збережені токени.

        :param user_id: ID користувача.
        :return: True, якщо токен успішно оновлено або не потребував оновлення, інакше False.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'refresh_access_token_if_needed' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def list_user_calendars(self, user_id: int) -> List[CalendarInfo]: # Змінено UUID на int
        """
        Перелічує всі календарі, доступні для підключеного облікового запису користувача.

        :param user_id: ID користувача.
        :return: Список об'єктів CalendarInfo.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'list_user_calendars' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def create_event(
        self, user_id: int, calendar_id: str, event_data: CalendarEventData # Змінено UUID на int
    ) -> Optional[CalendarEventData]:
        """
        Створює нову подію в указаному календарі користувача.

        :param user_id: ID користувача.
        :param calendar_id: ID календаря, в якому створюється подія.
        :param event_data: Дані події (Pydantic модель CalendarEventData).
        :return: Створена подія CalendarEventData або None у разі помилки.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'create_event' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def get_event(
        self, user_id: int, calendar_id: str, event_id: str # Змінено UUID на int
    ) -> Optional[CalendarEventData]:
        """
        Отримує конкретну подію з календаря користувача.

        :param user_id: ID користувача.
        :param calendar_id: ID календаря.
        :param event_id: ID події.
        :return: Дані події CalendarEventData або None.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'get_event' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def update_event(
        self, user_id: int, calendar_id: str, event_id: str, event_data: CalendarEventData # Змінено UUID на int
    ) -> Optional[CalendarEventData]:
        """
        Оновлює існуючу подію в календарі користувача.

        :param user_id: ID користувача.
        :param calendar_id: ID календаря.
        :param event_id: ID події для оновлення.
        :param event_data: Нові дані для події.
        :return: Оновлена подія CalendarEventData або None.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'update_event' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def delete_event(
        self, user_id: int, calendar_id: str, event_id: str # Змінено UUID на int
    ) -> bool:
        """
        Видаляє подію з календаря користувача.

        :param user_id: ID користувача.
        :param calendar_id: ID календаря.
        :param event_id: ID події для видалення.
        :return: True, якщо видалення успішне, інакше False.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'delete_event' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def list_events(
        self, user_id: int, calendar_id: str, start_time: datetime, end_time: datetime, # Змінено UUID на int
        query: Optional[str] = None
    ) -> List[CalendarEventData]:
        """
        Перелічує події з конкретного календаря в заданому часовому діапазоні.

        :param user_id: ID користувача.
        :param calendar_id: ID календаря.
        :param start_time: Початковий час діапазону.
        :param end_time: Кінцевий час діапазону.
        :param query: Опціональний рядок для пошуку серед подій.
        :return: Список об'єктів CalendarEventData.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'list_events' не реалізовано для {self.__class__.__name__}")

    # --- Приклади допоміжних методів для управління токенами ---
    # (Мають бути реалізовані в конкретних класах або в іншому базовому класі/сервісі для токенів інтеграцій)
    # TODO: Визначити модель та сервіс для зберігання токенів інтеграції (наприклад, UserIntegrationCredentialService).
    # async def _get_user_tokens(self, user_id: UUID) -> Optional[Dict[str, Any]]:
    #     """Заглушка: Отримує збережені токени для користувача та цього сервісу."""
    #     service_name_val = getattr(self, 'service_name', 'НевідомийСервіс')
    #     logger.warning(f"Заглушка отримання токенів: Не знайдено збережених токенів для користувача {user_id} та сервісу {service_name_val}.")
    #     return None

    # async def _store_user_tokens(self, user_id: UUID, tokens: Dict[str, Any], token_expires_at: Optional[datetime]) -> bool:
    #     """Заглушка: Зберігає/оновлює токени для користувача та цього сервісу."""
    #     service_name_val = getattr(self, 'service_name', 'НевідомийСервіс')
    #     logger.info(f"Заглушка зберігання токенів: Збереження токенів для користувача {user_id}, сервіс {service_name_val}.")
    #     return True

logger.info("BaseCalendarIntegrationService (ABC) та Pydantic моделі CalendarEventData/CalendarInfo визначено.")
