# backend/app/src/core/permissions.py

"""
Цей модуль визначає більш гранульовану логіку перевірки дозволів, можливо,
як залежності FastAPI або викликані класи/функції. Він базується на автентифікації
користувача, що надається `core.dependencies`.
"""

from functools import wraps
from typing import Callable, List, Optional, Any, Coroutine, Type # Додано Type для підказки Enum
from enum import Enum # Додано для прикладу require_roles

from fastapi import Depends, HTTPException, status, Request

# Поки що використовуємо UserModel-заповнювач з core.dependencies.
# Замініть на фактичний імпорт: from backend.app.src.models.auth import User as UserModel
from backend.app.src.core.dependencies import get_current_active_user, UserModel # get_current_user_optional знадобився б для AllowAll з опціональною автентифікацією

# Поки що використовуємо GroupRole-заповнювач з core.dicts.
# Замініть на фактичний імпорт, якщо відрізняється: from backend.app.src.core.dicts import GroupRole
from backend.app.src.core.dicts import GroupRole

# Заповнювач для фактичної сесії бази даних та репозиторію/сервісу членства в групах
# from backend.app.src.config.database import AsyncSession, get_db
# from backend.app.src.repositories.groups import GroupMembershipRepository # Приклад

class Permission:
    """Базовий клас для визначення дозволу."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        raise NotImplementedError("Перевірка дозволу не реалізована.")

class IsAuthenticated(Permission):
    """Дозволяє доступ лише автентифікованим користувачам."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        return user is not None and user.is_active

class IsSuperuser(Permission):
    """Дозволяє доступ лише суперкористувачам."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        return user is not None and user.is_active and hasattr(user, 'is_superuser') and user.is_superuser

class IsGroupAdmin(Permission):
    """
    Дозволяє доступ лише користувачам, які є адміністраторами конкретної групи.
    Цей дозвіл вимагає передачі `group_id` до `PermissionDependency`.
    """
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        if not (user and user.is_active):
            return False

        group_id = kwargs.get("group_id")
        if group_id is None:
            # Це вказує на помилку конфігурації у використанні дозволу.
            # У реальній програмі цю помилку слід належним чином залогувати.
            # print("Помилка: group_id не надано для перевірки дозволу IsGroupAdmin.")
            return False

        # Логіка-заповнювач для перевірки статусу адміністратора групи.
        # У реальній програмі це включало б запит до бази даних:
        # async with get_db() as db_session:
        #     membership_repo = GroupMembershipRepository(db_session)
        #     membership = await membership_repo.get_by_user_and_group(user_id=user.id, group_id=group_id)
        #     return membership is not None and membership.role == GroupRole.ADMIN

        # Для цілей заповнювача:
        # Якщо користувач є суперкористувачем, надати адміністративний доступ до будь-якої групи для тестування.
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return True
        # Імітація: користувач 1 є адміністратором групи 1, користувач 2 - групи 2 і т.д.
        # Це дуже спрощено і лише для демонстрації.
        if hasattr(user, 'id') and user.id == group_id:
            # print(f"Користувач {user.id} вважається адміністратором групи {group_id} (логіка-заповнювач)")
            return True

        # print(f"Користувач {user.id} НЕ є адміністратором групи {group_id} (логіка-заповнювач)")
        return False

class AllowAll(Permission):
    """Дозволяє доступ будь-якому користувачеві, включаючи анонімних (якщо попередня автентифікація не застосовується)."""
    async def has_permission(self, request: Request, user: Optional[UserModel], **kwargs: Any) -> bool:
        # Якщо використовується get_current_active_user, user не буде None, якщо ця залежність не змінена.
        # Якщо використовується опціональна автентифікація (get_current_user_optional), то user може бути None.
        return True

# --- Фабрика залежностей дозволів ---

def PermissionDependency(
    permissions: List[Permission],
    require_all: bool = True,
    allow_superuser_override: bool = True
) -> Callable[..., Coroutine[Any, Any, UserModel]]:
    """
    Залежність FastAPI, яка перевіряє, чи має поточний користувач необхідні дозволи.

    Args:
        permissions (List[Permission]): Список екземплярів дозволів для перевірки.
        require_all (bool): Якщо True, всі дозволи зі списку повинні бути виконані.
                            Якщо False, повинен бути виконаний принаймні один дозвіл.
        allow_superuser_override (bool): Якщо True, суперкористувач обходить усі інші перевірки дозволів.

    Returns:
        Викликана залежність FastAPI.
    """
    async def _permission_checker(
        request: Request,
        user: UserModel = Depends(get_current_active_user) # Гарантує, що користувач активний
        # Якщо вам потрібно підтримувати опціональну автентифікацію для деяких дозволів (наприклад, AllowAll з конкретними перевірками):
        # user: Optional[UserModel] = Depends(get_current_user_optional) # Потребує get_current_user_optional
    ) -> UserModel:
        # get_current_active_user вже викликає 401, якщо не автентифіковано або неактивно
        # Отже, об'єкт user тут завжди повинен бути активним екземпляром UserModel.

        # Обхід для суперкористувача
        if allow_superuser_override and hasattr(user, 'is_superuser') and user.is_superuser:
            return user

        # Витягти параметри шляху для дозволів, яким вони можуть знадобитися (наприклад, group_id)
        path_params = request.path_params

        results = []
        for perm_instance in permissions:
            # Передати path_params або відповідні частини до has_permission
            # Для IsGroupAdmin очікується 'group_id' у kwargs
            kwargs_for_perm = {}
            if isinstance(perm_instance, IsGroupAdmin) and 'group_id' in path_params:
                try:
                    kwargs_for_perm['group_id'] = int(path_params['group_id'])
                except ValueError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний формат group_id у шляху.")

            # Для AllowAll, user може бути None, якщо використовувалася опціональна залежність автентифікації.
            # Однак, з get_current_active_user, user гарантовано існує.
            # Якщо AllowAll є єдиним дозволом, ця перевірка тут дещо зайва,
            # але збережена для логічної повноти структури класу Permission.
            has_perm = await perm_instance.has_permission(request, user, **kwargs_for_perm)
            results.append(has_perm)

        if not results: # Не повинно статися, якщо список дозволів не порожній
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Не було перевірено жодних дозволів."
            )

        if require_all and not all(results):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостатньо дозволів для виконання цієї дії."
            )
        if not require_all and not any(results):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас немає жодного з необхідних дозволів для цієї дії."
            )
        return user
    return _permission_checker

# Приклад простішого декоратора дозволів на основі ролей (не класовий дозвіл)
# Це альтернативний або доповнюючий підхід.

def require_roles(allowed_roles: List[Union[str, Enum]]): # Дозволити також члени Enum
    """
    Декоратор для обмеження доступу користувачам з певними ролями.
    Припускає, що об'єкт user має атрибут `roles` (наприклад, List[str] або List[UserRoleEnum]).
    Це концептуальний приклад; для FastAPI краще зробити це залежністю.
    """
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            # Це спрощений приклад. У FastAPI 'user' надходив би з Depends()
            user: Optional[UserModel] = kwargs.get('user') # Або 'current_user' залежно від назви аргументу

            if not user or not hasattr(user, 'roles'): # Перевірити, чи має користувач атрибут 'roles'
                # print("Об'єкт user або user.roles не знайдено для перевірки @require_roles.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ролі користувача недоступні або користувача не надано.")

            user_roles = getattr(user, 'roles')
            if not isinstance(user_roles, list):
                # print(f"user.roles не є списком: {user_roles}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Атрибут ролей користувача неправильно налаштований.")

            # Перетворити allowed_roles на їхні значення, якщо вони є Enum
            allowed_role_values = [role.value if isinstance(role, Enum) else role for role in allowed_roles]

            # Перевірити, чи будь-яка з ролей користувача (також конвертуючи, якщо вони є Enum) відповідає дозволеним ролям
            user_has_role = False
            for user_role in user_roles:
                user_role_value = user_role.value if isinstance(user_role, Enum) else user_role
                if user_role_value in allowed_role_values:
                    user_has_role = True
                    break

            if not user_has_role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Потрібна одна з ролей: {allowed_role_values}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    print("--- Основні дозволи ---")
    print("Цей модуль визначає класи дозволів та фабрику залежностей для FastAPI.")

    # Макети об'єктів користувачів для демонстрації
    active_user = UserModel(id=1, email="user@example.com", is_active=True)
    setattr(active_user, 'roles', ["user"]) # Додати ролі для демонстрації require_roles

    inactive_user = UserModel(id=2, email="inactive@example.com", is_active=False)
    setattr(inactive_user, 'roles', ["user"])


    superuser_model = UserModel(id=3, email="super@example.com", is_active=True, is_superuser=True)
    setattr(superuser_model, 'roles', ["superuser", "user", "admin"])


    # Користувач для тестування адміністратора групи; заповнювач: користувач ID 4 є адміністратором групи 4
    admin_group1_user = UserModel(id=4, email="admin_g1@example.com", is_active=True)
    setattr(admin_group1_user, 'roles', ["group_admin", "user"])


    # Макет об'єкта запиту
    mock_request_group1 = Request(scope={"type": "http", "method": "GET", "path": "/groups/1/items", "path_params": {"group_id": "1"}})
    mock_request_group4 = Request(scope={"type": "http", "method": "GET", "path": "/groups/4/items", "path_params": {"group_id": "4"}})


    async def run_permission_check(perm_class, user, request_obj, **perm_kwargs):
        perm = perm_class()
        try:
            # Імітація того, як PermissionDependency передаватиме kwargs з path_params
            # Для IsGroupAdmin, group_id надходить з request.path_params, якщо не в perm_kwargs
            final_kwargs = perm_kwargs.copy()
            if isinstance(perm, IsGroupAdmin) and 'group_id' not in final_kwargs and 'group_id' in request_obj.path_params:
                 final_kwargs['group_id'] = int(request_obj.path_params['group_id'])

            has_perm = await perm.has_permission(request_obj, user, **final_kwargs)
            print(f"Перевірка користувача '{user.email if user else 'Anonymous'}' для {perm.__class__.__name__} (шлях: {request_obj.url.path}, kwargs: {final_kwargs}): {'НАДАНО' if has_perm else 'ВІДМОВЛЕНО'}")
        except Exception as e:
            print(f"Помилка перевірки {perm.__class__.__name__} для '{user.email if user else 'Anonymous'}': {e}")

    # Для тесту декоратора require_roles
    @require_roles(["admin", GroupRole.ADMIN]) # GroupRole.ADMIN це "admin"
    async def decorated_func_for_admin(user: UserModel): # Змінено назву аргументу на 'user'
        print(f"Користувач '{user.email}' отримав доступ до функції, призначеної лише для адміністраторів.")

    @require_roles(["user"])
    async def decorated_func_for_user(user: UserModel):
        print(f"Користувач '{user.email}' отримав доступ до функції, призначеної лише для користувачів.")

    import asyncio

    async def main():
        print("\n--- Тестування класів дозволів ---")
        print("\nТестування IsAuthenticated:")
        await run_permission_check(IsAuthenticated, active_user, mock_request_group1)
        await run_permission_check(IsAuthenticated, inactive_user, mock_request_group1) # Відмовлено (неактивний)
        # await run_permission_check(IsAuthenticated, None, mock_request_group1) # Завершиться невдачею в PermissionDependency через get_current_active_user

        print("\nТестування IsSuperuser:")
        await run_permission_check(IsSuperuser, active_user, mock_request_group1) # Відмовлено
        await run_permission_check(IsSuperuser, superuser_model, mock_request_group1) # Надано

        print("\nТестування IsGroupAdmin (логіка-заповнювач):")
        # Користувач ID 4 є адміністратором групи 4 за логікою-заповнювачем
        await run_permission_check(IsGroupAdmin, admin_group1_user, mock_request_group4) # Надано (користувач 4, група 4)
        await run_permission_check(IsGroupAdmin, admin_group1_user, mock_request_group1) # Відмовлено (користувач 4, група 1)
        await run_permission_check(IsGroupAdmin, superuser_model, mock_request_group1, group_id=99) # Суперкористувачу надано для групи 99

        print("\nТестування AllowAll:")
        await run_permission_check(AllowAll, active_user, mock_request_group1)
        # await run_permission_check(AllowAll, None, mock_request_group1) # Якщо використовується опціональна автентифікація

        print("\n--- Тестування декоратора @require_roles (концептуальне) ---")
        print("Примітка: Цей декоратор є спрощеним прикладом для прямих викликів.")
        try:
            await decorated_func_for_admin(user=superuser_model) # Суперкористувач має роль 'admin'
        except HTTPException as e:
            print(f"Доступ до адмін-функції для суперкористувача: {e.detail}")

        try:
            await decorated_func_for_admin(user=active_user) # active_user не має ролі 'admin'
        except HTTPException as e:
            print(f"Доступ до адмін-функції для active_user: {e.detail}")

        try:
            await decorated_func_for_user(user=active_user) # active_user має роль 'user'
        except HTTPException as e:
            print(f"Доступ до користувацької функції для active_user: {e.detail}")

        user_without_roles = UserModel(id=5, email="noroles@example.com", is_active=True)
        try:
            await decorated_func_for_user(user=user_without_roles)
        except HTTPException as e:
            print(f"Доступ до користувацької функції для user_without_roles: {e.detail}")


        print("\nПримітка: Фабрика PermissionDependency використовувалася б у залежностях ендпоінтів FastAPI.")
        print("Приклад: `Depends(PermissionDependency([IsAuthenticated(), IsGroupAdmin()]))`")

    asyncio.run(main())
