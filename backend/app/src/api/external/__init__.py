# backend/app/src/api/external/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету API, призначених для взаємодії з зовнішніми системами (вебхуки).

Цей пакет містить роутери для прийому та обробки вебхуків від різних
зовнішніх сервісів, таких як:
- Календарні сервіси (Google Calendar, Outlook Calendar).
- Месенджери (Telegram, Viber, Slack, Teams).
- Таск-трекери (Jira, Trello).

Ці ендпоінти зазвичай не призначені для прямого використання клієнтськими
додатками (frontend), а слугують для інтеграції з іншими системами.
Вони можуть мати власні механізми автентифікації (наприклад, секретні токени).
"""

# TODO: Імпортувати та, можливо, агрегувати роутери з цього пакету.
# Наприклад:
# from backend.app.src.api.external.webhook import router as webhook_router # Загальний роутер
# from backend.app.src.api.external.calendar import router as calendar_webhook_router
# from backend.app.src.api.external.messenger import router as messenger_webhook_router
#
# external_api_router = APIRouter() # Можна створити окремий агрегуючий роутер тут
# external_api_router.include_router(webhook_router)
# external_api_router.include_router(calendar_webhook_router, prefix="/calendar")
# external_api_router.include_router(messenger_webhook_router, prefix="/messenger")
#
# __all__ = (
#     "external_api_router",
# )

# На даному етапі файл може містити переважно документацію.
# Конкретні роутери будуть визначені у відповідних файлах цього пакету.
pass
