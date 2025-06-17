# backend/app/src/services/integrations/viber_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime  # Додано для позначки часу в мок-відповіді

from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, але може бути потрібен для BaseService

from backend.app.src.services.integrations.messenger_base import (
    BaseMessengerIntegrationService,
    MessengerUserProfile,
    MessengerMessage,
    MessageSendCommand,
    MessageSendResponse
)
from backend.app.src.models.integrations.user_integration import UserIntegration  # Припустима модель для зберігання Viber User ID
from backend.app.src.config.settings import settings  # Для Viber Auth Token
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# TODO: Додати залежність: pip install viberbot (або viber-bot-python) або httpx
# from viberbot import Api
# from viberbot.api.bot_configuration import BotConfiguration
# from viberbot.api.messages import TextMessage # та інші типи повідомлень

# Назва сервісу та отримання конфігурації з налаштувань
VIBER_SERVICE_NAME = "VIBER"
# TODO: Переконатися, що VIBER_AUTH_TOKEN, VIBER_BOT_NAME, VIBER_BOT_AVATAR правильно налаштовані в settings.py
VIBER_AUTH_TOKEN = getattr(settings, 'VIBER_AUTH_TOKEN', None)
VIBER_BOT_NAME = getattr(settings, 'VIBER_BOT_NAME', 'YourAppViberBot')
VIBER_BOT_AVATAR = getattr(settings, 'VIBER_BOT_AVATAR', None)  # URL до аватара бота
VIBER_API_BASE_URL = getattr(settings, 'VIBER_API_BASE_URL',
                             "https://chatapi.viber.com/pa")  # Використовується для прямих HTTP запитів


class ViberIntegrationService(BaseMessengerIntegrationService):
    """
    Конкретна реалізація для інтеграції з месенджером Viber.
    Обробляє надсилання повідомлень через Viber Bot API. Viber зазвичай використовує вебхуки для вхідних повідомлень.
    Фактичні виклики Viber API є заглушками і потребують повної реалізації.
    Примітка: API Viber може мати більше обмежень для ботів, що надсилають повідомлення користувачам
    без попередньої взаємодії або підписки, порівняно з Telegram або Slack.
    """
    service_name = VIBER_SERVICE_NAME

    def __init__(self, db_session: AsyncSession, user_id_for_context: Optional[UUID] = None):
        super().__init__(db_session, user_id_for_context)
        self.viber_client: Optional[Any] = None  # Заглушка для клієнта viberbot.Api

        if VIBER_AUTH_TOKEN:
            # from viberbot import Api
            # from viberbot.api.bot_configuration import BotConfiguration
            # bot_configuration = BotConfiguration(
            #     name=VIBER_BOT_NAME,
            #     avatar=VIBER_BOT_AVATAR, # URL до зображення аватара
            #     auth_token=VIBER_AUTH_TOKEN
            # )
            # self.viber_client = Api(bot_configuration)
            logger.info("Клієнт Viber був би ініціалізований тут з реальним токеном та конфігурацією.")
        else:
            logger.warning(
                "Автентифікаційний токен Viber не налаштовано. ViberIntegrationService використовуватиме мок-відповіді або не працюватиме.")
        logger.info(f"ViberIntegrationService ініціалізовано для користувача: {self.user_id_for_context or 'N/A'}.")

    async def connect_bot_or_webhook(self, app_settings: Dict[str, Any]) -> bool:
        """
        [ЗАГЛУШКА/TODO] Налаштовує вебхук для Viber бота.
        `app_settings` повинен містити `VIBER_WEBHOOK_URL`.
        """
        webhook_url = app_settings.get("VIBER_WEBHOOK_URL", getattr(settings, 'VIBER_WEBHOOK_URL', None))
        if not webhook_url or not VIBER_AUTH_TOKEN:
            logger.warning("URL вебхука Viber або Автентифікаційний токен не налаштовано. Неможливо встановити вебхук.")
            return False

        # if not self.viber_client:
        #     logger.error("Клієнт Viber не ініціалізовано, неможливо встановити вебхук.")
        #     return False
        # try:
        #     # event_types - список типів подій, на які бот хоче підписатися
        #     # success = self.viber_client.set_webhook(url=webhook_url, webhook_events=None) # None = всі події
        #     # if success:
        #     #    logger.info(f"Вебхук Viber успішно встановлено на URL: {webhook_url}")
        #     #    return True
        #     # else:
        #     #    logger.error(f"Не вдалося встановити вебхук Viber на URL: {webhook_url}")
        #     #    return False
        # except Exception as e:
        #     logger.error(f"Помилка при встановленні вебхука Viber: {e}", exc_info=True)
        #     return False
        logger.info(f"[ЗАГЛУШКА] Налаштування вебхука Viber викликано для URL: {webhook_url}. Припускаємо успіх.")
        return True

    async def disconnect_bot_or_webhook(self) -> bool:
        """[ЗАГЛУШКА/TODO] Видаляє вебхук для Viber бота (встановлює порожній URL)."""
        # if not self.viber_client:
        #     logger.error("Клієнт Viber не ініціалізовано, неможливо видалити вебхук.")
        #     return False
        # try:
        #     # Видалення вебхука шляхом надсилання порожнього рядка URL
        #     success = self.viber_client.set_webhook(url="")
        #     if success:
        #         logger.info("Вебхук Viber успішно видалено.")
        #         return True
        #     else:
        #         logger.error("Не вдалося видалити вебхук Viber.")
        #         return False
        # except Exception as e:
        #     logger.error(f"Помилка при видаленні вебхука Viber: {e}", exc_info=True)
        #     return False
        logger.info("[ЗАГЛУШКА] Видалення вебхука Viber викликано. Припускаємо успіх.")
        return True

    async def get_user_platform_id(self, user_id: UUID) -> Optional[str]:
        """[ЗАГЛУШКА/TODO] Отримує Viber User ID для користувача застосунку."""
        # TODO: Реалізувати отримання Viber User ID з моделі UserIntegration.
        # Viber User ID зазвичай отримується, коли користувач підписується на бота або надсилає йому повідомлення.
        # stmt = select(UserIntegration.platform_user_id).where(
        #     UserIntegration.user_id == user_id,
        #     UserIntegration.service_name == self.service_name,
        #     UserIntegration.is_active == True
        # )
        # record = (await self.db_session.execute(stmt)).scalar_one_or_none()
        # if record:
        #     logger.debug(f"Знайдено Viber User ID '{record}' для користувача {user_id}.")
        #     return str(record)
        logger.warning(f"[ЗАГЛУШКА] get_user_platform_id (Viber User ID) для користувача {user_id}. Повернення мок-ID.")
        # Viber User ID - це рядок, наприклад, "01234567890A="
        return f"mockViberUsrID{user_id.hex[:10].upper()}"

    async def send_message(self, command: MessageSendCommand) -> MessageSendResponse:
        """[ЗАГЛУШКА/TODO] Надсилає повідомлення в Viber."""
        viber_recipient_id = command.recipient_platform_id  # Це має бути Viber User ID
        message_text = command.message.text
        # TODO: Реалізувати конвертацію MessengerMessage в формат Viber (текст, кнопки, каруселі тощо).

        if not message_text:
            # i18n
            return MessageSendResponse(status="failed",
                                       error_message="Текст повідомлення не може бути порожнім для Viber.")

        # if not self.viber_client:
        #     logger.warning("Клієнт Viber не доступний для надсилання повідомлення.")
        #     # i18n
        #     return MessageSendResponse(status="failed", error_message="Клієнт Viber не налаштовано.")

        # try:
        #     # Для viber-bot-python, створення токена повідомлення для відстеження
        #     # message_token = self.viber_client.send_messages(to=viber_recipient_id, messages=[TextMessage(text=message_text)])
        #     # `send_messages` може повертати список токенів повідомлень або кидати виняток.
        #     # Успіх тут означає, що запит до API Viber був успішним, а не доставку.
        #     # platform_msg_id = str(message_token[0]) if message_token else None # Приклад
        #     platform_msg_id = f"mock_viber_msg_token_{datetime.now().timestamp()}" # Заглушка ID
        #     logger.info(f"Повідомлення Viber успішно надіслано до {viber_recipient_id}. Токен повідомлення: {platform_msg_id}")
        #     return MessageSendResponse(status="success", platform_message_id=platform_msg_id)
        # except Exception as e: # Загальний Exception, оскільки viber-bot-python може кидати різні помилки
        #     logger.error(f"Помилка Viber API при надсиланні повідомлення до {viber_recipient_id}: {e}", exc_info=True)
        #     return MessageSendResponse(status="failed", error_message=str(e))

        platform_msg_id = f"mock_viber_msg_token_{datetime.now().timestamp()}"
        logger.info(
            f"[ЗАГЛУШКА] Надсилання повідомлення Viber до {viber_recipient_id}: '{message_text[:50]}...'. Токен: {platform_msg_id}")
        # i18n
        return MessageSendResponse(status="success", platform_message_id=platform_msg_id, error_message=None)

    async def get_platform_user_profile(self, platform_user_id: str) -> Optional[MessengerUserProfile]:
        """[ЗАГЛУШКА/TODO] Отримує профіль користувача Viber за його platform_user_id."""
        logger.info(f"[ЗАГЛУШКА] Отримання профілю Viber для platform_id {platform_user_id}.")
        # TODO: Реалізувати виклик Viber API user/details (якщо доступно для ботів і є права).
        # Viber API для отримання деталей користувача може бути обмеженим.
        # if not self.viber_client: return None
        # try:
        #     user_details = self.viber_client.get_user_details(platform_user_id) # Метод з viber-bot-python
        #     if user_details and user_details.get('status') == 0: # status 0 - ok
        #         ud = user_details.get('user')
        #         return MessengerUserProfile(
        #             id=ud.get("id"),
        #             username=ud.get("name"), # Viber 'name' is often the user's display name
        #             full_name=ud.get("name"),
        #             # Додати інші поля: avatar=ud.get("avatar") тощо
        #         )
        #     else:
        #         logger.warning(f"Не вдалося отримати профіль Viber для {platform_user_id}: {user_details.get('status_message') if user_details else 'Невідома помилка'}")
        #         return None
        # except Exception as e:
        # ...
        if platform_user_id.startswith("mockViberUsrID"):
            return MessengerUserProfile(
                id=platform_user_id,
                username=f"MockViberUser_{platform_user_id[-6:].lower()}",
                full_name=f"Мок Користувач Viber {platform_user_id[-6:].lower()}"  # i18n
            )
        # i18n
        raise NotImplementedError(
            f"Метод 'get_platform_user_profile' не повністю реалізовано для {self.__class__.__name__}")


logger.info("ViberIntegrationService (сервіс інтеграції з Viber) клас визначено (реалізація-заглушка).")
