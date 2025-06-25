# backend/app/src/config/firebase.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування Firebase Admin SDK,
якщо Firebase використовується в проекті (наприклад, для Firebase Cloud Messaging (FCM)
або інших сервісів Firebase).
"""

import firebase_admin # type: ignore
from firebase_admin import credentials, messaging # type: ignore
from typing import Optional

# Імпорт налаштувань Firebase з settings.py
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger

# Глобальна змінна для зберігання статусу ініціалізації Firebase Admin SDK.
_firebase_app: Optional[firebase_admin.App] = None

def initialize_firebase_app() -> Optional[firebase_admin.App]:
    """
    Ініціалізує Firebase Admin SDK, якщо він ще не ініціалізований
    та якщо шлях до облікових даних вказано в налаштуваннях.
    Повертає екземпляр Firebase App або None, якщо ініціалізація не вдалася або не потрібна.
    """
    global _firebase_app

    # Перевіряємо, чи Firebase вже ініціалізовано (щоб уникнути повторної ініціалізації)
    if not firebase_admin._apps: # Або перевіряти _firebase_app
        # firebase_admin._apps - це словник ініціалізованих додатків Firebase.
        # Якщо він порожній, значить, ще не було ініціалізації.

        # TODO: Додати FirebaseSettings в settings.py, якщо ще немає.
        # Приклад:
        # class FirebaseSettings(BaseSettings):
        #     FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(None, description="Шлях до файлу Firebase Admin SDK JSON")
        #     # ... інші налаштування Firebase ...
        #     model_config = SettingsConfigDict(env_prefix='FIREBASE_', ...)
        #
        # settings.firebase: Optional[FirebaseSettings]

        firebase_creds_path: Optional[str] = None
        if hasattr(settings, 'firebase') and settings.firebase:
            firebase_creds_path = settings.firebase.FIREBASE_CREDENTIALS_PATH

        if firebase_creds_path:
            try:
                logger.info(f"Спроба ініціалізації Firebase Admin SDK з файлу: {firebase_creds_path}")
                cred = credentials.Certificate(firebase_creds_path)
                _firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK успішно ініціалізовано.")
            except FileNotFoundError:
                logger.error(f"Файл облікових даних Firebase не знайдено за шляхом: {firebase_creds_path}")
                _firebase_app = None
            except ValueError as e: # Може виникнути, якщо файл JSON некоректний
                logger.error(f"Помилка формату файлу облікових даних Firebase: {e}")
                _firebase_app = None
            except Exception as e:
                logger.error(f"Невідома помилка при ініціалізації Firebase Admin SDK: {e}")
                _firebase_app = None
        else:
            logger.warning("Шлях до облікових даних Firebase (FIREBASE_CREDENTIALS_PATH) не вказано. Firebase Admin SDK не буде ініціалізовано.")
            _firebase_app = None

    elif firebase_admin._apps and _firebase_app is None:
        # Якщо firebase_admin._apps не порожній, але наш _firebase_app ще None,
        # то, можливо, ініціалізація відбулася десь інде.
        # Спробуємо отримати дефолтний додаток.
        try:
            _firebase_app = firebase_admin.get_app()
            logger.info("Firebase Admin SDK вже було ініціалізовано, отримано існуючий екземпляр.")
        except Exception as e:
             logger.warning(f"Не вдалося отримати існуючий екземпляр Firebase App: {e}")
             _firebase_app = None

    return _firebase_app

# Функція для отримання ініціалізованого Firebase App.
# Може викликатися при старті додатку або при першому використанні.
def get_firebase_app() -> Optional[firebase_admin.App]:
    """Повертає ініціалізований екземпляр Firebase App або None."""
    if _firebase_app is None and not firebase_admin._apps:
        # Якщо наш _firebase_app ще не встановлено і глобальний firebase_admin._apps порожній,
        # то викликаємо ініціалізацію.
        return initialize_firebase_app()
    elif _firebase_app:
        return _firebase_app
    elif firebase_admin._apps: # Якщо _firebase_app is None, але _apps не порожній
        try:
            return firebase_admin.get_app() # Спробувати отримати дефолтний
        except:
            return None # Не вдалося
    return None


# Функції для роботи з Firebase сервісами, наприклад, FCM.
# Ці функції повинні викликатися лише після успішної ініціалізації.

# async def send_fcm_message(registration_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
#     """
#     Надсилає FCM повідомлення на вказаний токен реєстрації пристрою.
#     """
#     app = get_firebase_app()
#     if not app:
#         logger.error("Firebase не ініціалізовано. Неможливо надіслати FCM повідомлення.")
#         return False
#
#     message = messaging.Message(
#         notification=messaging.Notification(
#             title=title,
#             body=body,
#         ),
#         data=data, # Додаткові дані для обробки на клієнті
#         token=registration_token,
#     )
#
#     try:
#         response = messaging.send(message, app=app) # Явно вказуємо app
#         logger.info(f"FCM повідомлення успішно надіслано: {response}")
#         return True
#     except firebase_admin.exceptions.FirebaseError as e:
#         logger.error(f"Помилка надсилання FCM повідомлення: {e}")
#         # TODO: Обробка конкретних помилок (наприклад, Unregistered, InvalidArgument)
#         # if isinstance(e, messaging.UnregisteredError): ...
#         return False
#     except Exception as e:
#         logger.error(f"Невідома помилка при надсиланні FCM: {e}")
#         return False

# TODO: Додати FirebaseSettings в `backend/app/src/config/settings.py`, якщо ще не додано.
# Це включатиме `FIREBASE_CREDENTIALS_PATH`.
#
# TODO: Викликати `initialize_firebase_app()` при старті FastAPI додатку (в `main.py` в `startup` event),
# якщо Firebase використовується.
#
# @app.on_event("startup")
# async def startup_event():
#     initialize_firebase_app()
#
# Це гарантує, що SDK ініціалізується один раз.
#
# Якщо Firebase не використовується, цей модуль може залишатися порожнім або
# `initialize_firebase_app` просто повертатиме `None` без помилок,
# якщо `FIREBASE_CREDENTIALS_PATH` не задано.
# Поточна реалізація робить саме так.
#
# Функції типу `send_fcm_message` краще винести в окремий сервіс
# (наприклад, `backend/app/src/services/notifications/providers/fcm_provider.py`),
# який буде використовувати `get_firebase_app()` для отримання ініціалізованого додатку.
# Тут залишаємо лише логіку ініціалізації.
#
# Все виглядає як базова заглушка для налаштування Firebase.
# Головне - це наявність `FIREBASE_CREDENTIALS_PATH` в налаштуваннях.
#
# Перевірка `if not firebase_admin._apps:` є стандартним способом перевірки,
# чи вже був ініціалізований якийсь Firebase додаток, щоб уникнути помилки
# "Firebase App named '[DEFAULT]' already exists".
#
# Все готово для базового налаштування Firebase.
