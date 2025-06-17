# backend/app/src/services/integrations/messenger_base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession  # Для потенційної взаємодії з БД (токени/налаштування)

from backend.app.src.services.base import BaseService  # Опціонально: успадкувати, якщо потрібна сесія БД для спільних завдань
from backend.app.src.models.auth.user import User  # Для контексту користувача (не використовується прямо тут, але в підкласах)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

from pydantic import BaseModel, Field  # Використовуємо Pydantic для структур даних


# TODO: Розглянути переміщення Pydantic моделей MessengerUserProfile, MessengerMessage, MessageSendCommand, MessageSendResponse
#  до відповідного файлу схем, наприклад, backend/app/src/schemas/integrations/messenger.py

class MessengerUserProfile(BaseModel):
    """
    Pydantic модель для уніфікованого представлення профілю користувача месенджера.
    """
    id: str = Field(...,
                    description="ID користувача, специфічний для платформи (наприклад, Telegram chat_id, Slack user_id)")  # i18n
    username: Optional[str] = Field(None, description="Ім'я користувача (username) на платформі, якщо є")  # i18n
    full_name: Optional[str] = Field(None, description="Повне ім'я користувача на платформі, якщо є")  # i18n
    # TODO: Додати інші загальні поля, які можуть бути корисними (наприклад, avatar_url)


class MessengerMessage(BaseModel):
    """
    Pydantic модель для уніфікованого представлення повідомлення для надсилання.
    """
    text: Optional[str] = Field(None, description="Текстовий вміст повідомлення")  # i18n
    # TODO: Додати підтримку для вкладень, кнопок, швидких відповідей тощо.
    # attachments: Optional[List[Any]] = Field(None, description="Список вкладень (зображення, файли тощо)") # i18n
    # quick_replies: Optional[List[Dict[str, str]]] = Field(None, description="Список швидких відповідей") # i18n
    # buttons: Optional[List[Dict[str, Any]]] = Field(None, description="Список інтерактивних кнопок") # i18n


class MessageSendCommand(BaseModel):
    """
    Pydantic модель команди для надсилання повідомлення.
    """
    recipient_platform_id: str = Field(...,
                                       description="ID отримувача, специфічний для платформи (ID користувача або каналу)")  # i18n
    message: MessengerMessage = Field(..., description="Об'єкт повідомлення для надсилання")  # i18n
    # delivery_options: Optional[Dict[str, Any]] = Field(None, description="Додаткові параметри доставки (напр. silent notification)") # i18n


class MessageSendResponse(BaseModel):
    """
    Pydantic модель відповіді після надсилання повідомлення.
    """
    status: str = Field(..., description="Статус надсилання ('success', 'failed', 'pending')")  # i18n
    platform_message_id: Optional[str] = Field(None,
                                               description="ID повідомлення на зовнішній платформі, якщо є")  # i18n
    error_message: Optional[str] = Field(None, description="Повідомлення про помилку, якщо статус 'failed'")  # i18n


class BaseMessengerIntegrationService(BaseService, ABC):
    """
    Абстрактний базовий клас для сервісів інтеграції з платформами месенджерів.
    Визначає спільний інтерфейс для надсилання повідомлень, обробки вебхуків (концептуально)
    та управління підключеннями/ботами для платформ типу Telegram, Slack, Viber, Teams.

    Конкретні реалізації оброблятимуть взаємодію API та автентифікацію, специфічні для платформи.
    Може потребувати зберігання токенів ботів, ID користувачів платформи або ID каналів,
    потенційно в моделі UserIntegration або спеціалізованій моделі MessengerSubscription.
    """

    service_name: str  # Має бути визначено в підкласах, наприклад, "TELEGRAM", "SLACK"

    def __init__(self, db_session: AsyncSession, user_id_for_context: Optional[int] = None): # Змінено UUID на int
        """
        Ініціалізує сервіс з сесією БД та опціонально user_id для контексту.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param user_id_for_context: ID користувача для контексту операцій.
        """
        super().__init__(db_session)
        self.user_id_for_context = user_id_for_context
        logger.info(
            f"BaseMessengerIntegrationService (підклас: {self.__class__.__name__}) ініціалізовано для користувача: {self.user_id_for_context or 'N/A'}.")

    @abstractmethod
    async def connect_bot_or_webhook(self, settings_data: Dict[str, Any]) -> bool:  # Змінено settings на settings_data
        """
        Ініціалізує з'єднання бота або налаштовує вебхук для отримання повідомлень.
        Може включати реєстрацію URL вебхука на платформі або запуск клієнта бота.
        `settings_data` містить токени API, ім'я бота, URL вебхука тощо з конфігурації.
        Зазвичай це одноразове налаштування або завдання при старті системи.

        :param settings_data: Словник з налаштуваннями для підключення.
        :return: True, якщо підключення успішне, інакше False.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'connect_bot_or_webhook' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def disconnect_bot_or_webhook(self) -> bool:
        """
        Відключає бота або видаляє вебхук.

        :return: True, якщо відключення успішне, інакше False.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'disconnect_bot_or_webhook' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def get_user_platform_id(self, user_id: int) -> Optional[str]: # Змінено UUID на int
        """
        Отримує ID, специфічний для платформи месенджера, для даного користувача застосунку.
        Цей ID може зберігатися в UserIntegration або в спеціальному полі профілю користувача.
        Необхідний для надсилання прямих повідомлень користувачеві.

        :param user_id: ID користувача в застосунку.
        :return: Рядок з ID на платформі месенджера або None, якщо не знайдено.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # TODO: Реалізувати логіку отримання platform_id з UserIntegration або подібної моделі.
        # i18n
        raise NotImplementedError(f"Метод 'get_user_platform_id' не реалізовано для {self.__class__.__name__}")

    # @abstractmethod # Цей функціонал може бути частиною UserIntegrationService або подібного
    # async def link_platform_user_to_app_user(self, platform_user_id: str, app_user_id: UUID, platform_user_details: MessengerUserProfile) -> bool:
    #     """
    #     [Опціонально/Майбутнє] Пов'язує ID користувача платформи месенджера з ID користувача застосунку.
    #     Часто є частиною початкової взаємодії в чаті або потоку типу OAuth в месенджері.
    #     """
    #     raise NotImplementedError(f"Метод 'link_platform_user_to_app_user' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def send_message(self, command: MessageSendCommand) -> MessageSendResponse:
        """
        Надсилає повідомлення отримувачу на платформі месенджера.

        :param command: Об'єкт MessageSendCommand, що містить ID отримувача та вміст повідомлення.
        :return: Об'єкт MessageSendResponse, що вказує статус та ID повідомлення на платформі.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'send_message' не реалізовано для {self.__class__.__name__}")

    # Обробка вебхуків є складною та специфічною для платформи.
    # Загальний метод може бути надто високорівневим. Зазвичай, ендпоінти API викликають конкретні обробники.
    # @abstractmethod
    # async def handle_incoming_webhook(self, request_payload: Dict[str, Any], headers: Dict[str, Any]) -> Any:
    #     """
    #     [Опціонально/Майбутнє] Обробляє вхідне повідомлення або подію з вебхука платформи месенджера.
    #     Включає парсинг даних, ідентифікацію користувача/чату, типу повідомлення та виклик відповідних дій.
    #     """
    #     raise NotImplementedError(f"Метод 'handle_incoming_webhook' не реалізовано для {self.__class__.__name__}")

    @abstractmethod
    async def get_platform_user_profile(self, platform_user_id: str) -> Optional[MessengerUserProfile]:
        """
        Отримує інформацію про профіль користувача з платформи месенджера за його ID на платформі.
        Доступність та вміст залежать від API платформи та дозволів.

        :param platform_user_id: ID користувача на платформі месенджера.
        :return: Об'єкт MessengerUserProfile або None, якщо не знайдено або помилка.
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'get_platform_user_profile' не реалізовано для {self.__class__.__name__}")

    # Заглушка для управління токенами/конфігурацією самого сервісу (наприклад, токен бота)
    # async def _get_service_config(self) -> Optional[Dict[str, Any]]:
    #     """Заглушка: Завантажує конфігурацію сервісу (наприклад, токен бота) з settings.py."""
    #     service_name_val = getattr(self, 'service_name', 'НевідомийСервіс')
    #     # Приклад: return global_settings.MESSENGER_CONFIGS.get(service_name_val)
    #     logger.warning(f"Конфігурація сервісу не реалізована для {service_name_val}")
    #     return None


logger.info("BaseMessengerIntegrationService (ABC) та загальні Pydantic моделі для месенджерів визначено.")
