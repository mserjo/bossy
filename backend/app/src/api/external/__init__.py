# backend/app/src/api/external/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'external' API.

Цей пакет призначений для ендпоінтів, які взаємодіють із зовнішніми
системами, зокрема для прийому вебхуків (webhooks).
Кожен тип зовнішнього сервісу або логічно пов'язана група вебхуків
може мати свій власний файл з роутером у цьому пакеті:
- `webhook.py`: Загальний ендпоінт для прийому вебхуків або агрегатор.
- `calendar.py`: Вебхуки від календарних сервісів.
- `messenger.py`: Вебхуки від месенджерів.
- `tracker.py`: Вебхуки від таск-трекерів.

Цей файл робить каталог 'external' пакетом Python. Він може агрегувати
та експортувати роутери для вебхуків, які потім підключаються до
головного API роутера в `backend.app.src.api.router.py`.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери для вебхуків від різних сервісів,
# коли вони будуть створені у відповідних файлах цього пакету.
# from backend.app.src.api.external.webhook import router as generic_webhook_router # Загальний
# from backend.app.src.api.external.calendar import router as calendar_webhook_router
# from backend.app.src.api.external.messenger import router as messenger_webhook_router
# from backend.app.src.api.external.tracker import router as tracker_webhook_router

# Агрегуючий роутер для всіх зовнішніх API / вебхуків.
# Цей роутер буде підключений в `api/router.py` з префіксом, наприклад, `/external`.
router = APIRouter(tags=["v1 :: External Webhooks"]) # Тег може бути більш загальним, якщо не всі вебхуки для v1

# TODO: Розкоментувати та підключити окремі роутери.
# Кожен роутер може мати свій префікс відносно `/external`.
# Наприклад:
# router.include_router(generic_webhook_router, prefix="/hooks") # /external/hooks
# router.include_router(calendar_webhook_router, prefix="/calendar-hooks") # /external/calendar-hooks
# router.include_router(messenger_webhook_router, prefix="/messenger-hooks") # /external/messenger-hooks
# router.include_router(tracker_webhook_router, prefix="/tracker-hooks") # /external/tracker-hooks


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.router.py`.
# Наприклад, там може очікуватися `external_api_router` або `webhook_router`.
# TODO: Забезпечити належну безпеку для ендпоінтів вебхуків
# (перевірка підпису, секретних ключів, обмеження IP-адрес тощо).
# Ця логіка може бути реалізована як залежності FastAPI.
