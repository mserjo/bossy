# backend/app/src/api/v1/router.py
# -*- coding: utf-8 -*-
"""
Головний роутер для API версії 1 (v1).

Цей модуль відповідає за агрегацію всіх роутерів для окремих ресурсів (сутностей),
що належать до версії 1 API. Наприклад, сюди підключаються роутери для:
- Системних функцій (`system`)
- Автентифікації та управління профілем (`auth`)
- Довідників (`dictionaries`)
- Адміністративного управління користувачами (`users`)
- Груп (`groups`)
- Завдань та подій (`tasks`)
- Команд (`teams`)
- Бонусів, рахунків та нагород (`bonuses`)
- Гейміфікації (`gamification`)
- Звітів (`reports`)
- Сповіщень (`notifications`)
- Інтеграцій з зовнішніми сервісами (`integrations`)
- Файлів (`files`)

Цей роутер (`router`) потім імпортується в `backend.app.src.api.v1.__init__.py`
і далі в `backend.app.src.api.router.py` для підключення до головного API роутера
з відповідним префіксом (наприклад, `/v1`).
"""

from fastapi import APIRouter

# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати, якщо потрібне логування

# logger = get_logger(__name__) # TODO: Розкоментувати

# Ініціалізація роутера для API v1
router = APIRouter()

# TODO: Імпортувати та підключити роутери для кожної сутності API v1,
# коли відповідні файли та роутери в них будуть створені.
# Заглушки для імпортів:
# from backend.app.src.api.v1.system import router as system_v1_router
# from backend.app.src.api.v1.auth import router as auth_v1_router
# from backend.app.src.api.v1.dictionaries import router as dictionaries_v1_router
# from backend.app.src.api.v1.users import router as users_v1_router
# from backend.app.src.api.v1.groups import router as groups_v1_router
# from backend.app.src.api.v1.tasks import router as tasks_v1_router
# from backend.app.src.api.v1.teams import router as teams_v1_router
# from backend.app.src.api.v1.bonuses import router as bonuses_v1_router
# from backend.app.src.api.v1.gamification import router as gamification_v1_router
# from backend.app.src.api.v1.reports import router as reports_v1_router
# from backend.app.src.api.v1.notifications import router as notifications_v1_router
# from backend.app.src.api.v1.integrations import router as integrations_v1_router
# from backend.app.src.api.v1.files import router as files_v1_router

# Підключення роутерів (приклади, будуть активовані по мірі створення файлів):

# Системні ендпоінти (health, init_data, system settings для superadmin)
# router.include_router(system_v1_router, prefix="/system", tags=["v1 :: System"])
# logger.info("V1 System router included at /system")

# Автентифікація, реєстрація, управління профілем
# router.include_router(auth_v1_router, prefix="/auth", tags=["v1 :: Auth & Profile"])
# logger.info("V1 Auth & Profile router included at /auth")

# Довідники
# router.include_router(dictionaries_v1_router, prefix="/dictionaries", tags=["v1 :: Dictionaries"])
# logger.info("V1 Dictionaries router included at /dictionaries")

# Адміністративне управління користувачами (для superadmin)
# router.include_router(users_v1_router, prefix="/users", tags=["v1 :: Users (Admin)"])
# logger.info("V1 Users (Admin) router included at /users")

# Групи: створення, налаштування, членство, запрошення, шаблони, опитування
# router.include_router(groups_v1_router, prefix="/groups", tags=["v1 :: Groups"])
# logger.info("V1 Groups router included at /groups")

# Завдання: створення, призначення, виконання, пропозиції, відгуки
# Багато ендпоінтів завдань будуть вкладені в групи, наприклад: /groups/{group_id}/tasks
# Тому groups_v1_router може включати tasks_v1_router, або tasks_v1_router матиме префікс /groups/{group_id}/tasks
# Поки що припускаємо, що tasks_v1_router обробляє все, що стосується завдань.
# router.include_router(tasks_v1_router, prefix="/tasks", tags=["v1 :: Tasks & Events"])
# logger.info("V1 Tasks & Events router included at /tasks. Consider nesting under /groups/{group_id}")
# Або, якщо tasks_router визначає шляхи відносно /groups/{group_id}/tasks:
# router.include_router(tasks_v1_router, tags=["v1 :: Tasks & Events (nested in Groups)"]) # Префікс буде у groups_router

# Команди: створення, членство (в контексті групи)
# Аналогічно до завдань, команди зазвичай належать групам.
# router.include_router(teams_v1_router, prefix="/teams", tags=["v1 :: Teams"])
# logger.info("V1 Teams router included at /teams. Consider nesting under /groups/{group_id}")

# Бонуси: правила, рахунки, транзакції, нагороди
# router.include_router(bonuses_v1_router, prefix="/bonuses", tags=["v1 :: Bonuses & Rewards"])
# logger.info("V1 Bonuses & Rewards router included at /bonuses")

# Гейміфікація: рівні, бейджі, досягнення, рейтинги
# router.include_router(gamification_v1_router, prefix="/gamification", tags=["v1 :: Gamification"])
# logger.info("V1 Gamification router included at /gamification")

# Звіти
# router.include_router(reports_v1_router, prefix="/reports", tags=["v1 :: Reports"])
# logger.info("V1 Reports router included at /reports")

# Сповіщення: перегляд, шаблони, статуси доставки
# router.include_router(notifications_v1_router, prefix="/notifications", tags=["v1 :: Notifications"])
# logger.info("V1 Notifications router included at /notifications")

# Інтеграції: налаштування календарів, месенджерів, трекерів
# router.include_router(integrations_v1_router, prefix="/integrations", tags=["v1 :: Integrations"])
# logger.info("V1 Integrations router included at /integrations")

# Файли: завантаження аватарів, іконок
# router.include_router(files_v1_router, prefix="/files", tags=["v1 :: Files"])
# logger.info("V1 Files router included at /files")


# Приклад простого ендпоінту на кореневому рівні API v1 (наприклад, /api/v1/)
@router.get(
    "/",
    summary="Кореневий ендпоінт API v1",
    tags=["v1 :: System"],
    response_description="Базова інформація про API v1."
)
async def read_api_v1_root():
    """
    Кореневий ендпоінт для API версії 1.
    Надає базову інформацію про доступні ресурси v1 та статус.
    """
    # logger.debug("Запит на кореневий ендпоінт API v1")
    return {
        "message": "Ласкаво просимо до API версії 1 системи Bossy!",
        "version": "1.0.0", # TODO: Версію можна брати з конфігурації
        "status": "Активний",
        "documentation_url": "/docs",  # Відносно префіксу цього роутера (напр. /api/v1/docs)
        "redoc_url": "/redoc",      # Відносно префіксу цього роутера (напр. /api/v1/redoc)
        # TODO: Можна додати список основних доступних категорій ендпоінтів або посилання на документацію
    }

# Цей роутер (`router`) буде імпортований в `backend.app.src.api.v1.__init__.py`
# і далі в `backend.app.src.api.router.py` для підключення до головного API роутера.

# TODO: Переглянути та узгодити префікси для вкладених ресурсів (наприклад, завдання в групах).
# Можливо, деякі роутери (tasks, teams) не будуть підключатися тут напряму,
# а будуть включені в роутер груп (`groups_v1_router`) з відповідними префіксами.
# Наприклад, `groups_v1_router.include_router(tasks_specific_router, prefix="/{group_id}/tasks")`.
# Це залежить від обраної стратегії організації роутингу.
# Поточний `structure-claude-v3.md` передбачає окремі файли для ендпоінтів,
# наприклад, `backend/app/src/api/v1/groups/tasks.py` (якщо такий підхід буде),
# або ж `tasks.py` буде містити ендпоінти типу `router.get("/groups/{group_id}/tasks/{task_id}")`.
# Поки що залишаємо підключення на цьому рівні, але з коментарями про можливе вкладення.

# TODO: Додати специфічні для v1 обробники винятків або залежності, якщо це необхідно,
# хоча глобальні обробники та залежності часто є кращим рішенням.
# Наприклад, можна додати залежність, що перевіряє наявність певного заголовка для всіх запитів v1.
# from backend.app.src.api.v1.dependencies import check_v1_header
# router.dependencies.append(Depends(check_v1_header))
"""
Очікувана структура підключень в цьому файлі:
router = APIRouter()
router.include_router(system_v1_router, prefix="/system", tags=["v1 :: System"])
router.include_router(auth_v1_router, prefix="/auth", tags=["v1 :: Auth & Profile"])
... і так далі для всіх основних ресурсів API v1 ...
"""
