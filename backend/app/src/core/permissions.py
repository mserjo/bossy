# backend/app/src/core/permissions.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для реалізації системи дозволів та перевірки прав доступу.
Він може включати класи або функції-залежності FastAPI для перевірки,
чи має поточний користувач необхідні дозволи для виконання певної дії
або доступу до певного ресурсу.

Логіка дозволів може базуватися на:
- Ролях користувача (глобальних або в межах групи).
- Специфічних дозволах (permissions), призначених ролям або користувачам.
- Власності ресурсу (наприклад, користувач може редагувати лише свої дані).
"""

from fastapi import Depends, HTTPException
from typing import List, Optional, Callable, Any
import uuid

from backend.app.src.schemas.auth.user import UserSchema # Для отримання даних поточного користувача
from backend.app.src.core.dependencies import get_current_active_user # Залежність для отримання активного користувача
from backend.app.src.core.exceptions import ForbiddenException
from backend.app.src.core.constants import ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE, ROLE_USER_CODE
# Потрібні будуть сервіси для перевірки членства в групі та ролі в групі
# from backend.app.src.services.groups.membership_service import GroupMembershipService # Приклад
# from backend.app.src.config.database import get_db_session # Приклад
# from sqlalchemy.ext.asyncio import AsyncSession # Приклад

# --- Базовий клас для перевірки дозволів (якщо потрібна класова структура) ---
# class BasePermission:
#     """Базовий клас для класів дозволів."""
#     error_message: str = "Недостатньо прав для виконання цієї дії."
#
#     async def has_permission(self, user: Optional[UserSchema], **kwargs: Any) -> bool:
#         """
#         Метод, що перевіряє, чи має користувач дозвіл.
#         Повинен бути перевизначений у класах-наслідниках.
#         `kwargs` можуть містити додатковий контекст (наприклад, group_id, resource_id).
#         """
#         raise NotImplementedError("Метод has_permission має бути реалізований.")
#
#     def __call__(self, user: Optional[UserSchema] = Depends(get_optional_current_user), **kwargs: Any) -> Optional[UserSchema]:
#         """
#         Робить клас дозволу викликаним об'єктом (callable) для використання як залежність FastAPI.
#         Якщо перевірка не проходить, викликає ForbiddenException.
#         """
#         # Цей __call__ не зовсім правильний для асинхронної залежності.
#         # Краще використовувати функції-залежності.
#         # if not asyncio.run(self.has_permission(user=user, **kwargs)): # Погано викликати run в асинхронному коді
#         #     raise ForbiddenException(detail=self.error_message)
#         # return user
#         pass


# --- Функції-залежності для перевірки дозволів ---

# Приклад: Дозвіл лише для супер-адміністратора (вже є в dependencies.py як get_current_superuser)
# async def require_superuser(user: UserSchema = Depends(get_current_superuser)) -> UserSchema:
#     """Забезпечує, що поточний користувач є супер-адміністратором."""
#     return user


# Приклад: Дозвіл для адміністратора групи
# Ця функція потребуватиме `group_id` з шляху та доступу до БД для перевірки ролі.
# Це більш складна залежність, яка може бути реалізована тут або в `dependencies.py`.
# Поки що залишу як приклад концепції.
#
# async def require_group_admin(
#     group_id: uuid.UUID, # Отримується з параметра шляху FastAPI
#     user: UserSchema = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db_session) # Приклад, якщо потрібен доступ до БД
# ) -> UserSchema:
#     """
#     Перевіряє, чи є поточний користувач адміністратором вказаної групи
#     АБО супер-адміністратором (супер-адмін має доступ до всього).
#     """
#     if user.user_type_code == ROLE_SUPERADMIN_CODE:
#         return user # Супер-адмін має доступ
#
#     # Потрібна логіка для перевірки ролі користувача в групі group_id.
#     # Це може включати запит до GroupMembershipModel.
#     # membership_service = GroupMembershipService(db)
#     # user_role_in_group = await membership_service.get_user_role_in_group(user_id=user.id, group_id=group_id)
#     #
#     # if user_role_in_group is None or user_role_in_group.code != ROLE_ADMIN_CODE: # Припускаючи, що роль має поле code
#     #     raise ForbiddenException(detail=f"Ви не є адміністратором групи {group_id}.")
#
#     # TODO: Реалізувати реальну перевірку ролі в групі.
#     # Поки що, для прикладу, припустимо, що перевірка пройде, якщо не супер-адмін.
#     # Це НЕПРАВИЛЬНА логіка, лише для структури.
#     # raise ForbiddenException(detail="Перевірка ролі адміністратора групи ще не реалізована.") # Тимчасово
#     logger.warning(f"УВАГА: Перевірка ролі адміністратора групи ({group_id}) для користувача {user.id} ще не реалізована повністю в permissions.py.")
#     # Для проходження прикладу, якщо не супер-адмін, поки що не кидаємо помилку,
#     # але це має бути виправлено.
#     # У реальному коді тут має бути або виняток, або повернення user, якщо права є.
#     # Для демонстрації, якщо це не супер-адмін, припустимо, що він не адмін групи:
#     if user.user_type_code != ROLE_SUPERADMIN_CODE: # Зайва умова, бо вже перевірено
         # raise ForbiddenException(detail=f"Ви не є адміністратором групи {group_id} (тимчасова заглушка).")
#        pass # Поки що пропускаємо, щоб не блокувати
#     return user

# Приклад: Дозвіл для учасника групи
# async def require_group_member(
#     group_id: uuid.UUID,
#     user: UserSchema = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db_session)
# ) -> UserSchema:
#     """
#     Перевіряє, чи є поточний користувач учасником вказаної групи
#     АБО супер-адміністратором.
#     """
#     if user.user_type_code == ROLE_SUPERADMIN_CODE:
#         return user
#
#     # TODO: Реалізувати перевірку членства в групі.
#     # membership_service = GroupMembershipService(db)
#     # is_member = await membership_service.is_user_member_of_group(user_id=user.id, group_id=group_id)
#     # if not is_member:
#     #     raise ForbiddenException(detail=f"Ви не є учасником групи {group_id}.")
#     logger.warning(f"УВАГА: Перевірка членства в групі ({group_id}) для користувача {user.id} ще не реалізована повністю в permissions.py.")
#     # if user.user_type_code != ROLE_SUPERADMIN_CODE: # Зайва умова
          # raise ForbiddenException(detail=f"Ви не є учасником групи {group_id} (тимчасова заглушка).")
#         pass
#     return user


# --- Фабрика для створення залежностей з перевіркою списку ролей ---
# def require_roles(allowed_roles: List[str]) -> Callable[[UserSchema], UserSchema]:
#     """
#     Фабрика, що створює залежність FastAPI, яка перевіряє,
#     чи має поточний користувач одну з дозволених ролей (глобальних).
#     `allowed_roles` - список кодів ролей (наприклад, [ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE]).
#     """
#     async def role_checker(user: UserSchema = Depends(get_current_active_user)) -> UserSchema:
#         # Припускаємо, що UserSchema має поле `user_type_code` або список ролей.
#         # Якщо ролі в списку:
#         # user_roles_codes = [role.code for role in getattr(user, 'roles', [])]
#         # if not any(role_code in allowed_roles for role_code in user_roles_codes):
#         #     raise ForbiddenException(detail=f"Доступ дозволено лише для ролей: {', '.join(allowed_roles)}.")
#         #
#         # Якщо роль одна в user_type_code:
#         if user.user_type_code not in allowed_roles:
#             # Додаткова перевірка на супер-адміна, який має доступ до всього
#             if ROLE_SUPERADMIN_CODE not in allowed_roles and user.user_type_code == ROLE_SUPERADMIN_CODE:
#                 pass # Супер-адмін проходить, навіть якщо його роль не в списку (якщо це бажана поведінка)
#             else:
#                 raise ForbiddenException(detail=f"Доступ дозволено лише для ролей: {', '.join(allowed_roles)}.")
#         return user
#     return role_checker

# Приклад використання фабрики:
# require_admin_or_superuser = require_roles([ROLE_ADMIN_CODE, ROLE_SUPERADMIN_CODE])
# @app.get("/admin-stuff", dependencies=[Depends(require_admin_or_superuser)])
# async def get_admin_stuff(): ...


# TODO: Розробити більш детальну систему дозволів, якщо потрібно.
# Це може включати:
# - Модель `PermissionModel` (дозвіл, наприклад, "edit_group_settings", "delete_user").
# - Модель `RolePermissionModel` (зв'язок багато-до-багатьох між ролями та дозволами).
# - Модель `UserPermissionModel` (специфічні дозволи для користувача, що перевизначають роль).
# - Сервіси для перевірки цих дозволів.
#
# Поки що, система дозволів базується на перевірці `user_type_code` (для глобальних ролей типу superadmin)
# та на майбутніх перевірках ролей в контексті групи (group_admin, group_user),
# які будуть реалізовані в залежностях, що використовують `group_id`.
#
# Модуль `dependencies.py` вже містить `get_current_superuser`.
# Складніші залежності, що потребують `group_id` та доступу до БД для перевірки ролі в групі,
# можуть бути визначені тут або також в `dependencies.py`.
#
# `permissions.py` може містити більш абстрактні класи або функції для перевірки
# конкретних дій, наприклад:
#
# async def can_edit_group_settings(user: UserSchema, group_id: uuid.UUID, db: AsyncSession) -> bool:
#     # ... логіка перевірки ...
#     # Повертає True або False
#
# І потім залежність:
# async def require_can_edit_group_settings(
#     group_id: uuid.UUID,
#     user: UserSchema = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db_session)
# ):
#     if not await can_edit_group_settings(user, group_id, db):
#         raise ForbiddenException(detail="Ви не можете редагувати налаштування цієї групи.")
#     return user # Або нічого не повертати, якщо залежність лише для перевірки
#
# На даному етапі, цей файл може містити заглушки або приклади,
# оскільки повна реалізація системи дозволів - це велике завдання,
# що залежить від конкретних вимог до кожної дії та ресурсу.
#
# Поки що основні перевірки ролей (superuser) вже є в `dependencies.py`.
# Цей файл `permissions.py` залишено для можливого розширення більш гранулярними дозволами.
#
# Імпортую logger для використання в закоментованих прикладах.
from backend.app.src.config.logging import logger

# Все готово для базової структури.
# Фактична логіка дозволів буде додаватися по мірі реалізації ендпоінтів та сервісів.
# Наразі тут немає активного коду, окрім імпортів та коментарів-прикладів.
# Це відповідає структурі `structure-claude-v3.md`, де `permissions.py`
# вказаний для "реалізації системи дозволів та перевірки прав доступу".
# Поки що це місце для майбутньої реалізації.
# Залежності, що перевіряють конкретні ролі, вже є або будуть в `dependencies.py`.
# Цей файл може бути для більш складних, об'єктно-орієнтованих дозволів або правил.
# Наприклад, дозволи на рівні об'єктів (хто може редагувати конкретний запис).
#
# Залишаю файл з коментарями та прикладами, як зазначено в плані ("Частково в dependencies.py").
# Активний код для перевірки ролей вже є в `dependencies.py`.
#
# Все готово.
