# backend/app/src/models/auth/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для автентифікації та авторизації.

Цей пакет містить моделі даних, що стосуються користувачів, їхніх сесій,
токенів оновлення, ролей, дозволів та інших аспектів системи безпеки
та управління доступом додатку.

Моделі, визначені в цьому пакеті:
- `User`: Представляє користувача системи.
- `RefreshToken`: Зберігає токени оновлення для користувачів.
- `Session` (або `UserSession`): Зберігає інформацію про активні сесії користувачів.
- (Потенційно) `Role`, `Permission`, `UserRoleAssignment` та інші, якщо
  використовується більш гранулярна система ролей та дозволів.

Моделі з цього пакету експортуються для зручного доступу з інших частин програми,
наприклад, при визначенні залежностей FastAPI, у сервісному шарі або в репозиторіях.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт моделей з відповідних файлів цього пакету
from backend.app.src.models.auth.user import User
from backend.app.src.models.auth.token import RefreshToken
from backend.app.src.models.auth.session import UserSession # Перейменовано для уникнення конфлікту з SQLAlchemy Session

# TODO: Модель UserAvatar буде імпортовано, коли файл `backend/app/src/models/files/file.py`
#       (або аналогічний, що містить FileModel/UserAvatarModel) буде створено/оновлено.
#       Приклад: from backend.app.src.models.files import UserAvatarModel

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.auth import *`.
# Це допомагає контролювати публічний API пакету.
__all__ = [
    "User",
    "RefreshToken",
    "UserSession", # Оновлено назву
    # "UserAvatarModel", # Додати після реалізації та імпорту
]

logger.debug("Ініціалізація пакету моделей `auth`...")

# Примітка щодо UserAvatar:
# Модель UserAvatar, хоч і логічно пов'язана з користувачем (User),
# ймовірно, буде визначена в модулі, що стосується управління файлами
# (наприклад, `backend/app/src/models/files/file.py` або `avatar.py`),
# оскільки вона представляє запис про файл.
# У моделі `User` буде визначено зв'язок (relationship) до цієї моделі.
# Якщо `UserAvatarModel` ре-експортується звідси, це робиться для зручності,
# але її основне визначення буде в пакеті `files`.
