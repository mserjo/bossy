# backend/app/src/api/v1/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'dictionaries' API v1.

Цей пакет містить ендпоінти для роботи з довідниками системи в API v1.
Довідники - це набори відносно статичних даних, що використовуються
в різних частинах системи. Приклади довідників:
- Статуси (`statuses.py`)
- Ролі користувачів (`user_roles.py`)
- Типи груп (`group_types.py`)
- Типи завдань (`task_types.py`)
- Типи бонусів (`bonus_types.py`)
- Типи зовнішніх інтеграцій (`integration_types.py`)

Ендпоінти зазвичай надають можливість перегляду довідників.
Редагування довідників, як правило, доступне лише адміністраторам.

Цей файл робить каталог 'dictionaries' пакетом Python та експортує
агрегований роутер для всіх ендпоінтів довідників API v1.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери для кожного типу довідника,
# коли вони будуть створені у відповідних файлах цього пакету.
# from backend.app.src.api.v1.dictionaries.statuses import router as statuses_router
# from backend.app.src.api.v1.dictionaries.user_roles import router as user_roles_router
# from backend.app.src.api.v1.dictionaries.group_types import router as group_types_router
# from backend.app.src.api.v1.dictionaries.task_types import router as task_types_router
# from backend.app.src.api.v1.dictionaries.bonus_types import router as bonus_types_router
# from backend.app.src.api.v1.dictionaries.integration_types import router as integration_types_router

# Агрегуючий роутер для всіх ендпоінтів довідників API v1.
router = APIRouter(tags=["v1 :: Dictionaries"])

# TODO: Розкоментувати та підключити окремі роутери для кожного довідника.
# Кожен роутер матиме свій префікс відносно `/dictionaries`.
# Наприклад:
# router.include_router(statuses_router, prefix="/statuses")
# router.include_router(user_roles_router, prefix="/user-roles")
# router.include_router(group_types_router, prefix="/group-types")
# router.include_router(task_types_router, prefix="/task-types")
# router.include_router(bonus_types_router, prefix="/bonus-types")
# router.include_router(integration_types_router, prefix="/integration-types")

# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (там очікується `dictionaries_v1_router`).
