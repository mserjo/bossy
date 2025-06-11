# backend/app/src/services/integrations/teams_service.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession # Не використовується прямо, але може бути потрібен для BaseService

# Повні шляхи імпорту
from backend.app.src.services.integrations.messenger_base import (
    BaseMessengerIntegrationService,
    MessengerUserProfile,
    MessengerMessage,
    MessageSendCommand,
    MessageSendResponse
)
from backend.app.src.models.integrations.user_integration import UserIntegration # Для зберігання ID користувача Teams або посилань на розмову
from backend.app.src.config.settings import settings # Для Microsoft App ID, пароля/секрету для бота
from backend.app.src.config.logging import logger # Централізований логер

# TODO: Додати залежності: pip install botbuilder-core botbuilder-schema botframework-connector msgraph-sdk-python
# from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
# from botbuilder.schema import Activity, ActivityTypes, ConversationReference
# from botframework.connector.auth import MicrosoftAppCredentials

# Назва сервісу та отримання конфігурації з налаштувань
TEAMS_SERVICE_NAME = "TEAMS"
# TODO: Переконатися, що MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD, TEAMS_BOT_SERVICE_URL правильно налаштовані в settings.py
MICROSOFT_APP_ID = getattr(settings, 'MICROSOFT_APP_ID', None)
MICROSOFT_APP_PASSWORD = getattr(settings, 'MICROSOFT_APP_PASSWORD', None)
# TEAMS_BOT_SERVICE_URL використовується для створення ConversationReference для проактивних повідомлень,
# але може не бути потрібним, якщо використовуються інші методи Graph API для надсилання.
# Зазвичай це URL типу 'https://smba.trafficmanager.net/amer/'
TEAMS_BOT_SERVICE_URL = getattr(settings, 'TEAMS_BOT_SERVICE_URL', None)

class TeamsIntegrationService(BaseMessengerIntegrationService):
    """
    Конкретна реалізація для інтеграції з месенджером Microsoft Teams.
    Зазвичай включає використання Microsoft Bot Framework для проактивних повідомлень
    або Microsoft Graph API для деяких взаємодій.
    Фактичні виклики API є заглушками і потребують повної реалізації.
    """
    service_name = TEAMS_SERVICE_NAME

    def __init__(self, db_session: AsyncSession, user_id_for_context: Optional[UUID] = None):
        super().__init__(db_session, user_id_for_context)
        self.bot_adapter: Optional[Any] = None # Заглушка для BotFrameworkAdapter
        self.app_credentials: Optional[Any] = None # Заглушка для MicrosoftAppCredentials

        if MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD:
            # from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
            # from botframework.connector.auth import MicrosoftAppCredentials
            # self.app_credentials = MicrosoftAppCredentials(MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD)
            # self.bot_adapter = BotFrameworkAdapter(self.app_credentials)
            logger.info("BotFrameworkAdapter (Teams) був би ініціалізований тут з реальними обліковими даними.")
        else:
            logger.warning("Microsoft App ID/Пароль не налаштовано. TeamsIntegrationService використовуватиме мок-відповіді або не працюватиме.")
        logger.info(f"TeamsIntegrationService ініціалізовано для користувача: {self.user_id_for_context or 'N/A'}.")

    async def connect_bot_or_webhook(self, app_settings: Dict[str, Any]) -> bool: # app_settings може містити service_url тощо
        """
        [ЗАГЛУШКА/TODO] Ініціалізує з'єднання бота. Для Teams це перевірка конфігурації.
        """
        logger.info("[ЗАГЛУШКА] Teams connect_bot_or_webhook викликано. Перевірка конфігурації.")
        # TODO: Реалізувати перевірку можливості зв'язку з Bot Framework або Graph API (наприклад, тестовий запит).
        is_configured = bool(MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD)
        if is_configured:
            logger.info("Інтеграція з Teams виглядає налаштованою (App ID/Пароль присутні).")
        else:
            logger.warning("Інтеграція з Teams не має ключових конфігурацій (App ID або Пароль).")
        return is_configured

    async def disconnect_bot_or_webhook(self) -> bool:
        """[ЗАГЛУШКА/TODO] Відключає бота (для Teams це може нічого не робити)."""
        logger.info("[ЗАГЛУШКА] Teams disconnect_bot_or_webhook викликано.")
        # Для ботів на основі App ID/Password зазвичай не потрібно явного "відключення".
        return True

    async def get_user_platform_id(self, user_id: UUID) -> Optional[str]:
        """
        [ЗАГЛУШКА/TODO] Отримує Teams User AAD ID або Conversation ID для користувача застосунку.
        Потрібно для надсилання проактивних повідомлень.
        """
        # TODO: Реалізувати отримання Teams User AAD ID або ConversationReference.user.id
        # з моделі UserIntegration або подібної.
        # stmt = select(UserIntegration.platform_user_id).where( # Або інше поле для conversation_reference.user.id
        #     UserIntegration.user_id == user_id,
        #     UserIntegration.service_name == self.service_name,
        #     UserIntegration.is_active == True
        # )
        # platform_id_record = (await self.db_session.execute(stmt)).scalar_one_or_none()
        # if platform_id_record:
        #     logger.debug(f"Знайдено Teams User AAD ID/ConvRef User ID '{platform_id_record}' для користувача {user_id}.")
        #     return str(platform_id_record)
        logger.warning(f"[ЗАГЛУШКА] get_user_platform_id (Teams User AAD ID) для користувача {user_id}. Повернення мок-ID.")
        # Повертаємо мок AAD Object ID або Teams User ID (29:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        return f"mockTeamsAAD_{user_id.hex[:12].lower()}"

    async def send_message(self, command: MessageSendCommand) -> MessageSendResponse:
        """[ЗАГЛУШКА/TODO] Надсилає повідомлення в Microsoft Teams."""
        teams_recipient_id = command.recipient_platform_id # Це може бути AAD ID користувача, ID каналу, або Conversation ID
        message_text = command.message.text
        # TODO: Реалізувати конвертацію MessengerMessage в формат Teams (текст або Adaptive Card).

        if not message_text: # Teams може вимагати текст або картку
            # i18n
            return MessageSendResponse(status="failed", error_message="Текст повідомлення або картка не можуть бути порожніми для Teams.")

        # if not self.bot_adapter:
        #     logger.warning("Адаптер BotFramework (Teams) не доступний для надсилання повідомлення.")
        #     # i18n
        #     return MessageSendResponse(status="failed", error_message="Клієнт Teams не налаштовано.")

        # TODO: Реальна логіка надсилання повідомлення через Bot Framework або Graph API.
        # Для Bot Framework:
        # 1. Створити ConversationReference (потрібен service_url, user_id (teams), bot_id, conversation_id (каналу або чату)).
        #    Частину цих даних треба зберігати при першому контакті з користувачем/ботом.
        # 2. Використати self.bot_adapter.continue_conversation(reference, callback_method)
        #    де callback_method асинхронно надсилає активність:
        #    async def message_callback(turn_context: TurnContext):
        #        await turn_context.send_activity(Activity(type=ActivityTypes.message, text=message_text))
        # Для Graph API (надсилання в чат або канал):
        #    Потрібен відповідний graph_client та дозволи.

        platform_msg_id = f"mock_teams_activity_id_{uuid4()}"
        log_text = message_text[:50] if message_text else "повідомлення Adaptive Card"
        logger.info(f"[ЗАГЛУШКА] Надсилання повідомлення Teams до {teams_recipient_id}: '{log_text}...'. Activity ID: {platform_msg_id}")
        # i18n
        return MessageSendResponse(status="success", platform_message_id=platform_msg_id, error_message=None)

    async def get_platform_user_profile(self, platform_user_id: str) -> Optional[MessengerUserProfile]:
        """[ЗАГЛУШКА/TODO] Отримує профіль користувача Teams за його AAD ID (або іншим ID)."""
        logger.info(f"[ЗАГЛУШКА] Отримання профілю Teams для platform_id {platform_user_id}.")
        # TODO: Реалізувати виклик Microsoft Graph API для отримання інформації про користувача (/users/{platform_user_id}).
        # graph_client = await self._get_graph_api_client_for_app_perms() # Або делеговані права, якщо є
        # if not graph_client: return None
        # try:
        #    user_data = await graph_client.get(f"{MICROSOFT_GRAPH_API_BASE_URL}/users/{platform_user_id}")
        #    user_data.raise_for_status()
        #    ms_user = user_data.json()
        #    return MessengerUserProfile(
        #        id=ms_user.get("id"), # AAD Object ID
        #        username=ms_user.get("userPrincipalName"), # Usually email-like
        #        full_name=ms_user.get("displayName"),
        #        # email=ms_user.get("mail") # тощо
        #    )
        # except Exception as e:
        #    logger.error(f"Помилка отримання профілю Teams для {platform_user_id}: {e}", exc_info=True)
        #    return None

        if platform_user_id.startswith("mockTeamsAAD_"):
            return MessengerUserProfile(
                id=platform_user_id,
                username=f"user{platform_user_id.split('_')[-1]}@example.onmicrosoft.com",
                full_name=f"Мок Користувач Teams {platform_user_id.split('_')[-1]}" # i18n
            )
        # i18n
        raise NotImplementedError(f"Метод 'get_platform_user_profile' не повністю реалізовано для {self.__class__.__name__}")

logger.info("TeamsIntegrationService (сервіс інтеграції з Microsoft Teams) клас визначено (реалізація-заглушка).")
