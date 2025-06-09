# backend/app/src/api/v1/router.py
# -*- coding: utf-8 -*-
"""
Головний роутер для API версії 1 (v1).

Цей модуль визначає `v1_router` (екземпляр `APIRouter`), який агрегує
всі роутери для окремих функціональних блоків API v1, таких як:
- Системні ендпоінти (`system_router` з `api.v1.system.router`)
- Автентифікація та авторизація (`auth_router` з `api.v1.auth.router`)
- Керування користувачами (`users_router` з `api.v1.users.router`)
- Керування групами (`groups_router` з `api.v1.groups.router`)
- Керування завданнями (`tasks_router` з `api.v1.tasks.router`)
- та інші.

`v1_router` потім підключається до загального `api_router` в `app.src.api.router`.
"""

import logging
from fastapi import APIRouter

# Імпорт роутерів для окремих модулів v1.
# Ці файли та роутери будуть створені пізніше.
# Наприклад:
from .system import system_router # Очікуємо, що system_router експортується з api/v1/system/__init__.py
from .auth import auth_router # Імпортуємо агрегований auth_router з auth/__init__.py
from .users import users_router # Імпортуємо агрегований users_router з users/__init__.py
from .groups import groups_router # Імпортуємо агрегований groups_router з groups/__init__.py
from .tasks import tasks_router # Імпортуємо агрегований tasks_router з tasks/__init__.py
from .bonuses import bonuses_router # Імпортуємо агрегований bonuses_router з bonuses/__init__.py
from .gamification import gamification_router # Імпортуємо агрегований gamification_router з gamification/__init__.py
# from .notifications.router import router as notifications_router
# from .integrations.router import router as integrations_router
# from .files.router import router as files_router
# from .dictionaries.router import router as dictionaries_router


logger = logging.getLogger(__name__)

v1_router = APIRouter()

# Підключення роутера для системних ендпоінтів v1
# Коли `api/v1/system/router.py` та `system_router` в ньому будуть створені,
# наступний блок потрібно буде розкоментувати.
# try:
#     from .system.router import router as system_router # Перейменовано для уникнення конфлікту імен
#     v1_router.include_router(system_router, prefix="/system", tags=["V1 System"])
#     logger.info("Роутер v1.system підключено до v1_router.")
# except ImportError:
#     logger.warning("Не вдалося імпортувати system_router з api.v1.system.router. Системні ендпоінти v1 не будуть доступні.")
# logger.info("Концептуальне місце для підключення v1_router.system_router (з api.v1.system.router).") # Закоментуємо або видалимо цей рядок
try:
    # from .system.router import router as system_router # Якщо імпортуємо напряму з system/router.py
    from .system import system_router # Якщо system_router експортується з system/__init__.py
    v1_router.include_router(system_router, prefix="/system", tags=["V1 System"]) # Тег тут може бути зайвим, якщо вже є на system_router
    logger.info("Роутер v1.system підключено до v1_router з префіксом /system.")
except ImportError:
    logger.error("КРИТИЧНО: Не вдалося імпортувати system_router з api.v1.system. Системні ендпоінти v1 не будуть доступні.", exc_info=True)


# Приклади підключення інших роутерів (будуть розкоментовані по мірі їх створення):
try:
    # auth_router вже імпортовано вище
    v1_router.include_router(auth_router, prefix="/auth", tags=["V1 Authentication"])
    logger.info("Роутер v1.auth (агрегований) підключено з префіксом /auth.")
except ImportError:
    logger.warning("Не вдалося імпортувати auth_router з api.v1.auth. Ендпоінти автентифікації v1 не будуть доступні.")
except Exception as e:
    logger.error(f"Помилка підключення auth_router: {e}", exc_info=True)

# Підключення роутера для управління користувачами
try:
    # users_router вже імпортовано вище
    v1_router.include_router(users_router, prefix="/users", tags=["V1 User Management"])
    logger.info("Роутер v1.users (керування користувачами) підключено з префіксом /users.")
except ImportError: # Цей ImportError тут малоймовірний, якщо імпорт вгорі успішний
    logger.warning("Не вдалося імпортувати users_router з api.v1.users (мало б спрацювати з верхнього імпорту). Ендпоінти керування користувачами v1 не будуть доступні.")
except Exception as e:
    logger.error(f"Помилка підключення users_router: {e}", exc_info=True)

# Підключення роутера для управління задачами та подіями
try:
    # tasks_router вже імпортовано вище
    v1_router.include_router(tasks_router, prefix="/tasks", tags=["V1 Task & Event Management"])
    logger.info("Роутер v1.tasks (керування задачами та подіями) підключено з префіксом /tasks.")
except ImportError:
    logger.warning("Не вдалося імпортувати tasks_router з api.v1.tasks (мало б спрацювати з верхнього імпорту). Ендпоінти керування задачами та подіями v1 не будуть доступні.")
except Exception as e:
    logger.error(f"Помилка підключення tasks_router: {e}", exc_info=True)

# Підключення роутера для бонусної системи
try:
    # bonuses_router вже імпортовано вище
    v1_router.include_router(bonuses_router, prefix="/bonuses", tags=["V1 Bonus System"])
    logger.info("Роутер v1.bonuses (бонусна система) підключено з префіксом /bonuses.")
except ImportError:
    logger.warning("Не вдалося імпортувати bonuses_router з api.v1.bonuses (мало б спрацювати з верхнього імпорту). Ендпоінти бонусної системи v1 не будуть доступні.")
except Exception as e:
    logger.error(f"Помилка підключення bonuses_router: {e}", exc_info=True)

# try:
#     from .gamification.router import router as gamification_router
#     v1_router.include_router(gamification_router, prefix="/gamification", tags=["V1 Gamification"])
#     logger.info("Роутер v1.gamification підключено.")
# except ImportError: logger.warning("Роутер v1.gamification не знайдено.")

# try:
#     from .groups.router import router as groups_router
#     v1_router.include_router(groups_router, prefix="/groups", tags=["V1 Groups"])
#     logger.info("Роутер v1.groups підключено.")
# except ImportError: logger.warning("Роутер v1.groups не знайдено.")

# try:
#     from .tasks.router import router as tasks_router # Для завдань Kudos, подій тощо
#     v1_router.include_router(tasks_router, prefix="/kudos-tasks", tags=["V1 Kudos Tasks & Events"])
#     logger.info("Роутер v1.tasks (Kudos) підключено.")
# except ImportError: logger.warning("Роутер v1.tasks (Kudos) не знайдено.")

# try:
#     from .bonuses.router import router as bonuses_router
#     v1_router.include_router(bonuses_router, prefix="/bonuses", tags=["V1 Bonuses & Rewards"])
#     logger.info("Роутер v1.bonuses підключено.")
# except ImportError: logger.warning("Роутер v1.bonuses не знайдено.")

# try:
#     from .gamification.router import router as gamification_router
#     v1_router.include_router(gamification_router, prefix="/gamification", tags=["V1 Gamification"])
#     logger.info("Роутер v1.gamification підключено.")
# except ImportError: logger.warning("Роутер v1.gamification не знайдено.")

# try:
#     from .notifications.router import router as notifications_router # Для керування налаштуваннями сповіщень, історії тощо.
#     v1_router.include_router(notifications_router, prefix="/notifications-settings", tags=["V1 Notifications Settings"])
#     logger.info("Роутер v1.notifications підключено.")
# except ImportError: logger.warning("Роутер v1.notifications не знайдено.")

# try:
#     from .integrations.router import router as integrations_router # Для керування інтеграціями
#     v1_router.include_router(integrations_router, prefix="/integrations-management", tags=["V1 Integrations Management"])
#     logger.info("Роутер v1.integrations підключено.")
# except ImportError: logger.warning("Роутер v1.integrations не знайдено.")

# try:
#     from .files.router import router as files_router
#     v1_router.include_router(files_router, prefix="/files", tags=["V1 Files & Uploads"])
#     logger.info("Роутер v1.files підключено.")
# except ImportError: logger.warning("Роутер v1.files не знайдено.")


@v1_router.get("/ping", summary="Перевірка доступності API v1", tags=["V1 Health"])
async def ping_v1_api():
    """
    Простий ендпоінт для перевірки, чи роутер API v1 (`v1_router`) працює.
    Повертає статус "API v1 is alive!" та повідомлення "Pong from v1!".
    """
    logger.debug("API v1 ping ендпоінт викликано.")
    return {"status": "API v1 is alive!", "message": "Pong from v1!"}


logger.info("Головний роутер API v1 (`v1_router`) налаштовано з базовим ping ендпоінтом.")

# Експорт v1_router для використання в app.src.api.v1.__init__.py та app.src.api.router.py
# __all__ = ["v1_router"] # Необов'язково, якщо імпортується напряму як `from .router import v1_router`
                          # Якщо ж `from . import router` і потім `router.v1_router`, то __all__ не потрібен.
                          # Для простоти, часто використовують `from .router import v1_router`.
# У нашому випадку, ми будемо імпортувати як: from app.src.api.v1.router import v1_router
# Тому явно експортувати через __all__ не є критично необхідним.
# Залишимо змінну як `v1_router` для ясності при імпорті.
