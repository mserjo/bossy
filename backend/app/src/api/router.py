# backend/app/src/api/router.py
# -*- coding: utf-8 -*-
"""
Головний роутер API додатку.

Цей модуль відповідає за агрегацію всіх роутерів різних версій API
та роутерів для зовнішніх інтеграцій.
Він створює екземпляр `APIRouter` і підключає до нього:
- Роутер для API версії 1 (з `backend.app.src.api.v1.router`).
- Роутери для обробки вебхуків від зовнішніх систем (з `backend.app.src.api.external`).

Цей агрегований роутер потім імпортується та підключається до основного
FastAPI додатку в `backend.app.main.py`.
"""

from fastapi import APIRouter

# TODO: Розкоментувати, коли відповідні роутери будуть створені та налаштовані.
# Потрібно буде імпортувати роутер для v1 та роутери для external.
# Також потрібен доступ до `settings` для префіксів.
# from backend.app.src.api.v1.router import router as v1_api_router
# from backend.app.src.api.external.webhook import router as external_webhook_router
# # Приклади для інших зовнішніх роутерів, якщо вони будуть окремими:
# # from backend.app.src.api.external.calendar import router as calendar_router
# # from backend.app.src.api.external.messenger import router as messenger_router
# # from backend.app.src.api.external.tracker import router as tracker_router
# from backend.app.src.config.settings import settings
# from backend.app.src.config.logging import get_logger

# logger = get_logger(__name__)

# Ініціалізація головного роутера для всіх несуфіксованих API ендпоінтів.
# Цей роутер буде підключений в app.main.py, можливо, з префіксом типу /api.
router = APIRouter()

# Підключення роутера для API v1
# Префікс для v1 (наприклад, /v1) буде додано тут або в app.main.py.
# Якщо префікс додається в main.py (наприклад, app.include_router(api_router, prefix=settings.API_PREFIX)),
# тоді тут префікс для v1_api_router буде відносним (наприклад, settings.API_V1_STR, що може бути '/v1').
# TODO: Розкоментувати, коли v1_api_router буде готовий.
# router.include_router(
#     v1_api_router,
#     prefix=settings.API_V1_STR,  # Наприклад, "/v1"
#     tags=["v1"]
# )
# logger.info(f"Роутер для API v1 підключено з префіксом: {settings.API_V1_STR}")

# Підключення роутерів для зовнішніх API (вебхуків)
# Ці роутери можуть мати власні префікси.
# TODO: Розкоментувати та налаштувати префікси, коли роутери будуть готові.
# router.include_router(
#     external_webhook_router,
#     prefix="/external/webhooks",  # Приклад префіксу
#     tags=["External :: Webhooks"]
# )
# logger.info("Роутер для загальних вебхуків підключено з префіксом: /external/webhooks")

# router.include_router(
#     calendar_router,
#     prefix="/external/calendar",
#     tags=["External :: Calendar"]
# )
# logger.info("Роутер для вебхуків календаря підключено з префіксом: /external/calendar")

# router.include_router(
#     messenger_router,
#     prefix="/external/messenger",
#     tags=["External :: Messenger"]
# )
# logger.info("Роутер для вебхуків месенджерів підключено з префіксом: /external/messenger")

# router.include_router(
#     tracker_router,
#     prefix="/external/tracker",
#     tags=["External :: Tracker"]
# )
# logger.info("Роутер для вебхуків трекерів підключено з префіксом: /external/tracker")


# Приклад простого ендпоінту на рівні цього агрегованого роутера.
# Якщо цей роутер підключений в main.py з префіксом /api,
# то цей ендпоінт буде доступний за шляхом /api/ping.
@router.get(
    "/ping",
    summary="Перевірка доступності агрегованого API роутера",
    tags=["System", "Health Check"],
    response_description="Повідомлення про успішну роботу роутера"
)
async def ping_main_api_router():
    """
    Простий ендпоінт для перевірки, чи головний агрегований API роутер працює.
    Це може бути корисно для швидкої діагностики налаштувань маршрутизації.
    """
    # logger.debug("Запит на /ping агрегованого API роутера")
    return {"message": "Bossy API router is active and pingable!"}

# Важливо: GraphQL роутер (`graphql_app`) зазвичай підключається окремо
# в `app/main.py` на тому ж рівні, що й цей `router`,
# оскільки він має свій власний префікс (наприклад, /graphql) і може мати
# іншу логіку обробки запитів.

# TODO: Переглянути структуру префіксів. Можливо, `settings.API_V1_STR` вже включає `/api/v1`.
# В такому випадку, якщо `router` з `main.py` вже має префікс `/api`, то для `v1_api_router`
# префікс тут має бути просто `/v1`. Або ж `router` з `main.py` не має префіксу,
# а всі префікси визначаються тут. Потрібна консистентність.
# Поточний план передбачає, що `main.py` підключає цей `router` з префіксом `settings.API_V1_STR`,
# що може бути не зовсім логічно, якщо цей роутер агрегує і інші шляхи крім v1.
# Краще, щоб `main.py` підключав цей `router` наприклад, без префіксу або з `/api`,
# а вже тут визначалися префікси для `/v1`, `/external` тощо.
# Я залишу TODO для `main.py` щодо цього.

"""
Очікувана структура підключень в цьому файлі:
router = APIRouter()
router.include_router(v1_api_router, prefix="/v1", tags=["v1"]) # Якщо settings.API_V1_STR = "/v1"
router.include_router(external_webhook_router, prefix="/external/webhooks", tags=["External Webhooks"])
... інші роутери ...

А в main.py:
app.include_router(main_api_router_from_here, prefix="/api") # Де /api - це загальний префікс для REST API
Тоді шляхи будуть /api/v1/... , /api/external/webhooks/...
"""
