# backend/app/src/tasks/notifications/sms.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання відправки SMS сповіщень.

Визначає `SendSmsTask`, відповідальний за асинхронну відправку SMS.
"""

import asyncio
from typing import Any, Dict, Optional

from app.src.tasks.base import BaseTask
# from app.src.config.settings import settings # Для доступу до конфігурації SMS-шлюзу
# import httpx # Розкоментуйте, якщо будете використовувати httpx для реальної інтеграції

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Приклад конфігурації SMS-шлюзу (має бути винесено в settings та захищено)
# Ці значення є повністю фіктивними.
SMS_GATEWAY_API_KEY = "your_sms_gateway_api_key_placeholder" # settings.SMS_GATEWAY_API_KEY
SMS_GATEWAY_SENDER_ID = "KudosApp" # settings.SMS_GATEWAY_SENDER_ID
SMS_GATEWAY_URL = "https://api.smsgateway.example.com/send" # settings.SMS_GATEWAY_URL

class SendSmsTask(BaseTask):
    """
    Завдання для асинхронної відправки SMS сповіщень.

    УВАГА: Цей клас є заглушкою. Реальна відправка SMS потребує інтеграції
    з конкретним SMS-шлюзом (наприклад, Twilio, Vonage, інший місцевий провайдер).
    Логіка взаємодії з API шлюзу (HTTP запити, обробка відповідей)
    має бути реалізована в методі `_send_sms_via_gateway`.
    """

    def __init__(self, name: str = "SendSmsTask"):
        """
        Ініціалізація завдання відправки SMS.
        """
        super().__init__(name)
        self.api_key = SMS_GATEWAY_API_KEY
        self.sender_id = SMS_GATEWAY_SENDER_ID
        self.gateway_url = SMS_GATEWAY_URL
        # Для реальної інтеграції тут можна ініціалізувати HTTP клієнт, наприклад:
        # self.http_client = httpx.AsyncClient(timeout=10.0)
        # Або створити його тимчасово в _send_sms_via_gateway.

    async def _send_sms_via_gateway(self, phone_number: str, message: str) -> bool:
        """
        Заглушка для фактичної відправки SMS через API шлюзу.

        Args:
            phone_number (str): Номер телефону отримувача у міжнародному форматі.
            message (str): Текст SMS повідомлення.

        Returns:
            bool: True, якщо SMS було успішно прийнято шлюзом (або імітовано успіх),
                  False в іншому випадку.
        """
        self.logger.info(
            f"Спроба відправки SMS на номер '{phone_number}'. Текст: '{message[:50]}...' "
            f"(Використовується заглушка, реальна відправка НЕ відбувається)."
        )

        # --- Початок блоку реальної інтеграції (приклад з httpx) ---
        # # Переконайтеся, що httpx встановлено: pip install httpx
        # if not hasattr(self, 'http_client'): # Створення клієнта, якщо не створено в __init__
        #     self.http_client = httpx.AsyncClient(timeout=10.0)
        #
        # try:
        #     payload = {
        #         # Параметри залежать від конкретного SMS-шлюзу
        #         "key": self.api_key,
        #         "from": self.sender_id,
        #         "to": phone_number,
        #         "text": message,
        #         # "type": "unicode", # Наприклад, для підтримки українських символів
        #     }
        #     # Деякі шлюзи вимагають передачу API ключа в заголовках
        #     headers = {
        #         # "Authorization": f"Bearer {self.api_key}",
        #         # "Content-Type": "application/json" # або application/x-www-form-urlencoded
        #     }
        #
        #     # response = await self.http_client.post(self.gateway_url, json=payload, headers=headers)
        #     # Або для form data: response = await self.http_client.post(self.gateway_url, data=payload, headers=headers)
        #
        #     # response.raise_for_status() # Перевірка на HTTP помилки (4xx, 5xx)
        #
        #     # Обробка відповіді від шлюзу (залежить від формату відповіді шлюзу)
        #     # response_data = response.json()
        #     # if response_data.get("status") == "ok" or response.status_code == 200: # Приклад успішної відповіді
        #     #     self.logger.info(f"SMS на номер '{phone_number}' успішно прийнято шлюзом. Message ID: {response_data.get('message_id', 'N/A')}")
        #     #     return True
        #     # else:
        #     #     error_detail = response_data.get('error_text', response.text)
        #     #     self.logger.error(f"Помилка від SMS-шлюзу при відправці на '{phone_number}': {error_detail}")
        #     #     return False
        #
        # except httpx.HTTPStatusError as e:
        #     self.logger.error(f"HTTP помилка ({e.response.status_code}) при відправці SMS на '{phone_number}': {e.response.text}", exc_info=True)
        #     return False
        # except httpx.RequestError as e: # Помилки з'єднання, таймаути тощо.
        #     self.logger.error(f"Помилка запиту при відправці SMS на '{phone_number}' до {self.gateway_url}: {e}", exc_info=True)
        #     return False
        # except Exception as e: # Інші непередбачені помилки
        #     self.logger.error(f"Непередбачена помилка під час відправки SMS через шлюз на '{phone_number}': {e}", exc_info=True)
        #     return False
        # # finally:
        # #    # Якщо клієнт створюється тимчасово, його треба закрити
        # #    await self.http_client.aclose()
        # --- Кінець блоку реальної інтеграції ---

        # Імітація затримки мережі (0.1 - 0.5 секунди)
        await asyncio.sleep(0.1 + 0.4 * (hash(phone_number) % 100) / 100.0)

        # У цьому прикладі-заглушці ми завжди повертаємо True,
        # ніби SMS було успішно відправлено.
        # Для тестування обробки помилок можна додати умову, наприклад:
        # if "error" in message.lower() or phone_number.endswith("00"):
        #    self.logger.warning(f"Імітація помилки відправки SMS (заглушка) на номер '{phone_number}'.")
        #    return False

        self.logger.info(f"SMS на номер '{phone_number}' (заглушка) успішно 'відправлено'.")
        return True


    async def run(self, phone_number: str, message: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Виконує відправку SMS сповіщення.

        Args:
            phone_number (str): Номер телефону отримувача (бажано у міжнародному форматі,
                                 наприклад, +380XXXXXXXXX або 380XXXXXXXXX).
            message (str): Текст SMS повідомлення. Максимальна довжина залежить від шлюзу
                           та кодування (наприклад, 160 символів для GSM-7, 70 для UCS-2).
            **kwargs: Додаткові аргументи (наразі не використовуються).

        Returns:
            Dict[str, Any]: Результат операції, що містить {'sent': True/False,
                                                         'phone_number': str,
                                                         'error': Optional[str]}.
        """
        self.logger.info(f"Завдання '{self.name}' отримало запит на відправку SMS на номер '{phone_number}'.")

        if not phone_number or not isinstance(phone_number, str):
            error_msg = "Не надано або некоректний номер телефону для відправки SMS."
            self.logger.error(error_msg)
            return {"sent": False, "error": error_msg, "phone_number": str(phone_number)}

        if not message or not isinstance(message, str):
            error_msg = "Не надано або некоректний текст повідомлення для SMS."
            self.logger.error(error_msg)
            return {"sent": False, "error": error_msg, "phone_number": phone_number}

        # Тут можна додати валідацію номера телефону (наприклад, регулярним виразом)
        # та перевірку довжини повідомлення, якщо це не робить сам шлюз.
        # Наприклад: if not re.match(r"^\+?[1-9]\d{1,14}$", phone_number): ...

        success = await self._send_sms_via_gateway(phone_number, message)

        result = {"sent": success, "phone_number": phone_number}
        if not success:
            # Деталі помилки вже залоговані в _send_sms_via_gateway
            result["error"] = f"Не вдалося надіслати SMS на номер {phone_number}. Дивіться логи."
            # Якщо потрібно, щоб BaseTask.on_failure спрацював, можна прокинути виняток тут.
            # raise SmsSendingFailedError(f"Failed to send SMS to {phone_number}")

        return result

# # Приклад використання (можна видалити або закоментувати):
# # class SmsSendingFailedError(Exception): pass
# #
# # async def main():
# #     logging.basicConfig(
# #         level=logging.INFO,
# #         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# #     )
# #     sms_task = SendSmsTask()
# #
# #     logger.info("Тест 1: Відправка тестового SMS (буде використана заглушка)")
# #     result_test_1 = await sms_task.execute(
# #         phone_number="+380501234567", # Або інший формат, який очікує ваш шлюз
# #         message="Це тестове SMS повідомлення від Kudos System (SendSmsTask)."
# #     )
# #     logger.info(f"Результат тесту 1: {result_test_1}")
# #
# #     logger.info("\nТест 2: Відправка SMS з порожнім повідомленням")
# #     result_test_2 = await sms_task.execute(
# #         phone_number="+380507654321",
# #         message=""
# #     )
# #     logger.info(f"Результат тесту 2: {result_test_2}")
# #
# #     # Приклад імітації помилки (якщо реалізовано в заглушці _send_sms_via_gateway)
# #     # logger.info("\nТест 3: Імітація помилки відправки SMS")
# #     # result_error = await sms_task.execute(
# #     #     phone_number="+380500000000", # Наприклад, номер, що викликає помилку в заглушці
# #     #     message="Test SMS that should trigger an error in stub."
# #     # )
# #     # logger.info(f"Результат тесту 3: {result_error}")
# #
# # if __name__ == "__main__":
# #     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# #     asyncio.run(main())
