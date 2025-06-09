# backend/app/src/core/permissions.py
"""
Модуль перевірки дозволів для FastAPI програми Kudos.

Цей модуль визначає систему класів дозволів та залежностей FastAPI,
які використовуються для контролю доступу до різних ендпоінтів.
Він інтегрується з системою автентифікації (`core.dependencies`) для отримання
інформації про поточного користувача.

Основні компоненти:
- Базовий клас `Permission`: Абстрактний клас для всіх дозволів.
- Специфічні класи дозволів:
    - `IsAuthenticated`: Дозволяє доступ лише автентифікованим та активним користувачам.
    - `IsSuperuser`: Дозволяє доступ лише активним суперкористувачам.
    - `IsGroupAdmin`: (Заповнювач) Перевіряє, чи є користувач адміністратором вказаної групи.
                       Потребує реальної логіки взаємодії з БД.
    - `AllowAll`: Дозволяє доступ усім, включаючи анонімних користувачів (якщо не
                  вимагається попередня автентифікація на рівні ендпоінту).
- `PermissionDependency`: Фабрика залежностей FastAPI, яка перевіряє набір дозволів
                          для поточного користувача. Може вимагати всі дозволи або будь-який з них.
- `require_roles`: Декоратор (приклад) для перевірки ролей користувача.
                   Для FastAPI часто краще використовувати класові дозволи або залежності.

ВАЖЛИВО: `UserModel` імпортується з `core.dependencies` і наразі є заповнювачем.
Його потрібно буде оновити, коли реальна модель `User` буде доступна.
"""

from functools import wraps
from typing import Callable, List, Optional, Any, Coroutine, Type, Union as TypingUnion
from enum import Enum

from fastapi import Depends, HTTPException, status, Request

# TODO: Оновити імпорт UserModel, коли реальна модель буде доступна в backend.app.src.models.auth.user
from backend.app.src.core.dependencies import get_current_active_user, UserModel  # UserModel тут є заповнювачем
from backend.app.src.core.dicts import GroupRole  # Імпорт Enum для ролей в групі
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


# TODO: Розглянути імпорт реальної сесії БД та репозиторію/сервісу для GroupMembership, коли вони будуть доступні.
# from backend.app.src.config.database import AsyncSession, get_db
# from backend.app.src.repositories.groups.group_membership_repository import GroupMembershipRepository # Приклад шляху


class Permission:
    """
    Базовий абстрактний клас для визначення користувацьких дозволів.
    Кожен дозвіл повинен успадковувати цей клас та реалізовувати метод `has_permission`.
    """

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        """
        Асинхронний метод для перевірки, чи має користувач необхідний дозвіл.

        Args:
            request (Request): Об'єкт запиту FastAPI.
            user (UserModel): Об'єкт поточного користувача (або None для анонімних, якщо дозволено).
            **kwargs: Додаткові аргументи, які можуть бути передані з `PermissionDependency`
                      (наприклад, `group_id` з параметрів шляху).

        Returns:
            bool: True, якщо дозвіл надано, False в іншому випадку.

        Raises:
            NotImplementedError: Якщо метод не реалізований у підкласі.
        """
        raise NotImplementedError("Метод has_permission не реалізований у підкласі.")


class IsAuthenticated(Permission):
    """Дозвіл, що надає доступ лише автентифікованим та активним користувачам."""

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # Залежність get_current_active_user вже гарантує, що user існує та активний.
        # Цей клас підтверджує цей стан.
        # У випадку використання з опціональною автентифікацією, тут була б перевірка user is not None.
        is_permitted = user is not None and user.is_active
        logger.debug(
            f"IsAuthenticated: Користувач '{user.email if user else 'Анонімний'}', активний: {user.is_active if user else 'N/A'}. Дозвіл: {is_permitted}")
        return is_permitted


class IsSuperuser(Permission):
    """Дозвіл, що надає доступ лише активним суперкористувачам."""

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # get_current_active_user гарантує, що user активний.
        is_superuser = hasattr(user, 'is_superuser') and user.is_superuser
        is_permitted = user is not None and user.is_active and is_superuser
        logger.debug(f"IsSuperuser: Користувач '{user.email}', суперкористувач: {is_superuser}. Дозвіл: {is_permitted}")
        return is_permitted


class IsGroupAdmin(Permission):
    """
    Дозвіл, що надає доступ лише користувачам, які є адміністраторами (або власниками)
    конкретної групи. Цей дозвіл вимагає, щоб `group_id` було передано
    через `PermissionDependency` з параметрів шляху.
    """

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # get_current_active_user гарантує, що user активний.
        if not (user and user.is_active):  # Додаткова перевірка, хоча має бути гарантована
            logger.warning(f"IsGroupAdmin: Спроба перевірки для неактивного або неавтентифікованого користувача.")
            return False

        group_id = kwargs.get("group_id")
        if group_id is None:
            logger.error(
                "IsGroupAdmin: group_id не було надано для перевірки дозволу. Це помилка конфігурації шляху або залежності.")
            # У реальному сценарії це може вказувати на помилку розробника.
            # Можна повернути False або викликати внутрішню помилку сервера.
            return False  # Або raise HTTPException(status_code=500, detail="Помилка конфігурації дозволу")

        logger.debug(f"IsGroupAdmin: Перевірка користувача '{user.email}' (ID: {user.id}) для групи ID: {group_id}.")

        # --- TODO: Замінити логіку-заповнювач на реальну перевірку членства та ролі в групі ---
        # Ця логіка має використовувати репозиторій/сервіс для запиту до БД.
        # Наприклад:
        # db_session = kwargs.get("db") # Якщо сесію передано, або отримати її через get_db()
        # if not db_session: # Потрібно передати сесію в PermissionDependency або отримати її тут
        #     async for session in get_db(): # Отримати сесію, якщо не передано
        #         db_session = session
        #         break
        #
        # membership_repo = GroupMembershipRepository(db_session) # Потрібно створити/імпортувати
        # membership = await membership_repo.get_user_membership_in_group(user_id=user.id, group_id=group_id)
        # if membership and (membership.role == GroupRole.ADMIN or membership.role == GroupRole.OWNER):
        #     logger.info(f"IsGroupAdmin: Користувач '{user.email}' є '{membership.role.value}' групи {group_id}. Дозвіл надано.")
        #     return True
        # --- Кінець TODO ---

        # Поточна логіка-заповнювач:
        if hasattr(user, 'is_superuser') and user.is_superuser:
            logger.debug(
                f"IsGroupAdmin: Користувач '{user.email}' є суперкористувачем. Надано доступ до групи {group_id} (обхід).")
            return True
        # Імітація: користувач з ID X є адміністратором групи X.
        if hasattr(user, 'id') and user.id == group_id:
            logger.debug(
                f"IsGroupAdmin: Користувач ID {user.id} вважається адміністратором групи {group_id} (логіка-заповнювач). Дозвіл надано.")
            return True

        logger.info(
            f"IsGroupAdmin: Користувач '{user.email}' (ID: {user.id}) не є адміністратором групи {group_id} (за логікою-заповнювачем). Дозвіл відхилено.")
        return False


class AllowAll(Permission):
    """
    Дозвіл, що завжди надає доступ.
    Корисний для публічних ендпоінтів або коли контроль доступу обробляється іншим чином.
    Якщо використовується з `get_current_active_user`, то користувач буде автентифікований.
    Для справді публічного доступу (включаючи анонімних) потрібна опціональна автентифікація.
    """

    async def has_permission(self, request: Request, user: Optional[UserModel], **kwargs: Any) -> bool:
        logger.debug(f"AllowAll: Дозвіл надано для користувача '{user.email if user else 'Анонімний'}'.")
        return True


# --- Фабрика залежностей дозволів ---

def PermissionDependency(
        permissions: List[Type[Permission]],  # Очікуємо список класів дозволів, а не екземплярів
        require_all: bool = True,
        allow_superuser_override: bool = True
) -> Callable[..., Coroutine[Any, Any, UserModel]]:
    """
    Фабрика залежностей FastAPI, яка перевіряє набір дозволів для поточного користувача.

    Створює та повертає асинхронну функцію-залежність `_permission_checker`,
    яка використовується FastAPI для перевірки дозволів перед виконанням обробника шляху.

    Args:
        permissions (List[Type[Permission]]): Список класів дозволів (не екземплярів),
                                              які потрібно перевірити.
        require_all (bool): Якщо `True` (за замовчуванням), користувач повинен мати всі
                            вказані дозволи. Якщо `False`, достатньо мати хоча б один.
        allow_superuser_override (bool): Якщо `True` (за замовчуванням), суперкористувач
                                         автоматично проходить усі перевірки дозволів.

    Returns:
        Callable: Асинхронна функція-залежність для використання з `Depends()`.
    """
    # Створюємо екземпляри дозволів тут
    perm_instances = [perm_class() for perm_class in permissions]

    async def _permission_checker(
            request: Request,
            user: UserModel = Depends(get_current_active_user)
            # Якщо потрібна опціональна автентифікація для деяких сценаріїв:
            # user: Optional[UserModel] = Depends(get_current_user_optional) # Необхідно створити get_current_user_optional
    ) -> UserModel:
        # `get_current_active_user` вже викликає HTTPException(401), якщо користувач
        # не автентифікований або неактивний.

        # Обхід для суперкористувача, якщо ввімкнено
        if allow_superuser_override and hasattr(user, 'is_superuser') and user.is_superuser:
            logger.debug(f"Дозвіл автоматично надано суперкористувачу '{user.email}'.")
            return user

        # Вилучення параметрів шляху для передачі в `has_permission`
        path_params = request.path_params.copy()  # Копіюємо, щоб уникнути зміни оригіналу

        results = []
        for perm_instance in perm_instances:
            kwargs_for_perm = {}
            # Спеціальна обробка для IsGroupAdmin для передачі group_id
            if isinstance(perm_instance, IsGroupAdmin) and 'group_id' in path_params:
                try:
                    kwargs_for_perm['group_id'] = int(path_params['group_id'])
                except ValueError:
                    logger.warning(f"Недійсний формат group_id у шляху: '{path_params['group_id']}'.", exc_info=True)
                    # TODO i18n: Translatable message
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Недійсний формат ID групи у шляху.")

            # Передаємо `db` сесію, якщо вона потрібна для дозволу (наприклад, для запитів до БД)
            # TODO: Розглянути передачу db сесії до has_permission, якщо дозволи будуть робити запити до БД
            # async for db_session in get_db(): # Це створить нову сесію; краще передати існуючу, якщо можливо
            #     kwargs_for_perm['db'] = db_session
            #     break

            has_perm = await perm_instance.has_permission(request, user, **kwargs_for_perm)
            results.append(has_perm)

        if not results and permissions:  # Якщо список дозволів був не порожній, але результатів немає
            logger.error("Список дозволів для перевірки був порожній або не вдалося отримати результати.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Помилка конфігурації
                detail="Помилка конфігурації перевірки дозволів."  # TODO i18n: Translatable message
            )

        final_decision = all(results) if require_all else any(results)

        if not final_decision:
            logger.warning(
                f"Користувачу '{user.email}' відмовлено в доступі. "
                f"Результати перевірок: {results} (вимагалося {'всі' if require_all else 'будь-який'})."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостатньо прав для виконання цієї дії."  # TODO i18n: Translatable message
            )

        logger.debug(f"Користувачу '{user.email}' надано доступ. Результати перевірок: {results}.")
        return user

    return _permission_checker


# --- TODO: Оцінити доцільність використання декоратора @require_roles для FastAPI ---
# Хоча такий декоратор може бути корисним в інших контекстах, для FastAPI
# підхід з класами дозволів та `PermissionDependency` зазвичай є більш гнучким,
# краще інтегрується з системою залежностей FastAPI та легше тестується.
# Залишено для можливого обговорення або специфічних випадків.
def require_roles(allowed_roles: List[TypingUnion[str, Enum]]):
    """
    Декоратор для обмеження доступу ендпоінту користувачам з певними ролями.
    Припускає, що об'єкт `user`, переданий до обгорнутої функції, має атрибут `roles`,
    який є списком рядків або членів Enum, що представляють ролі користувача.

    Args:
        allowed_roles (List[Union[str, Enum]]): Список рядків або членів Enum, що представляють
                                                 дозволені ролі.
    """

    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            # У FastAPI 'user' зазвичай отримується через Depends(get_current_active_user)
            # і передається як аргумент функції обробника шляху.
            # Цей декоратор очікує, що 'user' буде серед kwargs або як позиційний аргумент,
            # що може бути не завжди так, якщо він не використовується як залежність FastAPI.
            user: Optional[UserModel] = kwargs.get('user') or next((arg for arg in args if isinstance(arg, UserModel)),
                                                                   None)

            if not user:
                logger.warning("@require_roles: Користувача не знайдено в аргументах функції. Доступ заборонено.")
                # TODO i18n: Translatable message
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Доступ заборонено: користувача не автентифіковано.")

            if not hasattr(user, 'roles'):
                logger.error(f"@require_roles: Об'єкт користувача '{user.email}' не має атрибута 'roles'.")
                # TODO i18n: Translatable message
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Помилка конфігурації ролей користувача.")

            user_roles_attr = getattr(user, 'roles')
            if not isinstance(user_roles_attr, list):
                logger.error(
                    f"@require_roles: Атрибут 'roles' користувача '{user.email}' не є списком (тип: {type(user_roles_attr)}).")
                # TODO i18n: Translatable message
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Неправильний формат ролей користувача.")

            # Перетворення значень Enum на рядки для порівняння
            allowed_role_values = [role.value if isinstance(role, Enum) else str(role) for role in allowed_roles]

            user_role_values = []
            for user_role in user_roles_attr:
                user_role_values.append(user_role.value if isinstance(user_role, Enum) else str(user_role))

            if not any(user_r_val in allowed_role_values for user_r_val in user_role_values):
                logger.warning(
                    f"@require_roles: Користувач '{user.email}' з ролями {user_role_values} не має жодної з дозволених ролей: {allowed_role_values}.")
                # TODO i18n: Translatable message (possibly with placeholder for roles)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Для доступу потрібна одна з наступних ролей: {', '.join(allowed_role_values)}")

            logger.debug(
                f"@require_roles: Користувач '{user.email}' з ролями {user_role_values} має доступ (дозволені: {allowed_role_values}).")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Блок для демонстрації та базового тестування при прямому запуску модуля.
if __name__ == "__main__":
    # Налаштування логування для тестування (якщо воно ще не налаштоване)
    try:
        from backend.app.src.config.logging import setup_logging

        setup_logging()
        logger.info("Логування налаштовано для тестування permissions.py.")
    except ImportError:
        import logging as base_logging

        base_logging.basicConfig(level=base_logging.INFO)  # Базове налаштування
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування.")

    logger.info("--- Демонстрація Модуля До дозовлів ---")
    logger.info("Цей модуль визначає класи дозволів та фабрику залежностей для FastAPI.")

    # Створення макетів об'єктів користувачів для демонстрації
    # TODO: Замінити UserModel на реальну модель, коли вона буде доступна.
    active_user_instance = UserModel(id=1, email="user@example.com", is_active=True)
    setattr(active_user_instance, 'roles', [GroupRole.MEMBER])  # Додаємо роль для тестування @require_roles

    inactive_user_instance = UserModel(id=2, email="inactive@example.com", is_active=False)
    setattr(inactive_user_instance, 'roles', [GroupRole.MEMBER])

    superuser_instance = UserModel(id=3, email="super@example.com", is_active=True, is_superuser=True)
    setattr(superuser_instance, 'roles', [SystemUserRole.SUPERUSER, GroupRole.ADMIN, GroupRole.MEMBER])

    # Користувач для тестування IsGroupAdmin; використовується логіка-заповнювач: користувач ID 4 є адміном групи 4
    group_admin_user_instance = UserModel(id=4, email="admin_g4@example.com", is_active=True)
    setattr(group_admin_user_instance, 'roles', [GroupRole.ADMIN])

    # Створення макетів об'єктів Request для тестування (для вилучення path_params)
    mock_request_no_params = Request(scope={"type": "http", "method": "GET", "path": "/items"})
    mock_request_group1_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/1/items", "path_params": {"group_id": "1"}})
    mock_request_group4_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/4/items", "path_params": {"group_id": "4"}})
    mock_request_invalid_group_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/abc/items", "path_params": {"group_id": "abc"}})


    async def run_permission_check_demo(perm_class: Type[Permission], user_instance: Optional[UserModel],
                                        request_obj: Request, **perm_kwargs):
        """Допоміжна функція для демонстрації перевірки дозволів."""
        perm = perm_class()
        perm_name = perm.__class__.__name__
        user_email = user_instance.email if user_instance else "Анонімний"

        # Імітація передачі параметрів шляху, як це робить PermissionDependency
        final_kwargs = perm_kwargs.copy()
        if isinstance(perm, IsGroupAdmin) and 'group_id' not in final_kwargs and 'group_id' in request_obj.path_params:
            try:
                final_kwargs['group_id'] = int(request_obj.path_params['group_id'])
            except ValueError:
                logger.error(
                    f"Тест {perm_name}: Некоректний group_id '{request_obj.path_params['group_id']}' для користувача '{user_email}'.")
                return  # Не продовжувати, якщо group_id невалідний

        try:
            has_perm = await perm.has_permission(request_obj, user_instance, **final_kwargs)
            logger.info(
                f"Тест {perm_name}: Користувач '{user_email}', шлях '{request_obj.url.path}', kwargs {final_kwargs}. Дозвіл: {'НАДАНО' if has_perm else 'ВІДМОВЛЕНО'}")
        except Exception as e:
            logger.error(f"Тест {perm_name}: Помилка під час перевірки для користувача '{user_email}': {e}",
                         exc_info=True)


    # Тестування декоратора @require_roles
    @require_roles([GroupRole.ADMIN, SystemUserRole.SUPERUSER])
    async def example_admin_required_function(user: UserModel):
        logger.info(
            f"Користувач '{user.email}' успішно виконав дію, що вимагає ролі адміністратора або суперкористувача.")


    @require_roles([GroupRole.MEMBER])
    async def example_member_required_function(user: UserModel):
        logger.info(f"Користувач '{user.email}' успішно виконав дію, що вимагає ролі учасника.")


    import asyncio


    async def main_test_permissions():
        """Основна асинхронна функція для запуску тестів дозволів."""
        logger.info("\n--- Тестування Класів Дозволів ---")

        logger.info("\nТестування IsAuthenticated:")
        await run_permission_check_demo(IsAuthenticated, active_user_instance, mock_request_no_params)
        await run_permission_check_demo(IsAuthenticated, inactive_user_instance,
                                        mock_request_no_params)  # Очікується: ВІДМОВЛЕНО (користувач неактивний)

        logger.info("\nТестування IsSuperuser:")
        await run_permission_check_demo(IsSuperuser, active_user_instance,
                                        mock_request_no_params)  # Очікується: ВІДМОВЛЕНО
        await run_permission_check_demo(IsSuperuser, superuser_instance, mock_request_no_params)  # Очікується: НАДАНО

        logger.info("\nТестування IsGroupAdmin (логіка-заповнювач):")
        await run_permission_check_demo(IsGroupAdmin, group_admin_user_instance,
                                        mock_request_group4_path)  # Очікується: НАДАНО (користувач 4, група 4)
        await run_permission_check_demo(IsGroupAdmin, group_admin_user_instance,
                                        mock_request_group1_path)  # Очікується: ВІДМОВЛЕНО (користувач 4, група 1)
        await run_permission_check_demo(IsGroupAdmin, superuser_instance,
                                        mock_request_group1_path)  # Очікується: НАДАНО (суперкористувач має доступ до будь-якої групи)
        await run_permission_check_demo(IsGroupAdmin, active_user_instance,
                                        mock_request_group1_path)  # Очікується: ВІДМОВЛЕНО
        await run_permission_check_demo(IsGroupAdmin, active_user_instance,
                                        mock_request_invalid_group_path)  # Повинен обробити помилку ValueError

        logger.info("\nТестування AllowAll:")
        await run_permission_check_demo(AllowAll, active_user_instance, mock_request_no_params)
        await run_permission_check_demo(AllowAll, None, mock_request_no_params)  # Тест з анонімним користувачем

        logger.info("\n--- Тестування Декоратора @require_roles (концептуальне) ---")
        logger.info("Примітка: Декоратор тестується з прямими викликами, передаючи 'user'.")
        try:
            await example_admin_required_function(user=superuser_instance)
        except HTTPException as e:
            logger.error(f"Тест @require_roles (superuser_instance для admin_required): {e.detail}")

        try:
            await example_admin_required_function(user=active_user_instance)
        except HTTPException as e:
            logger.warning(
                f"Тест @require_roles (active_user_instance для admin_required): {e.detail} (ОЧІКУВАНА ВІДМОВА)")

        try:
            await example_member_required_function(user=active_user_instance)
        except HTTPException as e:
            logger.error(f"Тест @require_roles (active_user_instance для member_required): {e.detail}")

        user_without_any_roles = UserModel(id=5, email="noroles@example.com", is_active=True)
        # setattr(user_without_any_roles, 'roles', []) # Якщо атрибут roles є, але порожній
        try:
            # Якщо атрибут 'roles' взагалі відсутній, буде помилка атрибута раніше,
            # але @require_roles також перевіряє наявність атрибута.
            await example_member_required_function(user=user_without_any_roles)
        except HTTPException as e:
            logger.warning(
                f"Тест @require_roles (user_without_any_roles для member_required): {e.detail} (ОЧІКУВАНА ВІДМОВА)")

        logger.info("\nДемонстрація завершена. Перевірте вивід логів для деталей.")
        logger.info(
            "Пам'ятайте, що PermissionDependency та класи дозволів зазвичай використовуються в Depends() в ендпоінтах FastAPI.")


    asyncio.run(main_test_permissions())
