# backend/app/src/core/permissions.py
# -*- coding: utf-8 -*-
# # Модуль системи дозволів для FastAPI програми Kudos (Virtus).
# #
# # Цей модуль визначає гнучку систему класів дозволів та залежностей FastAPI,
# # що використовуються для контролю доступу до різних ендпоінтів та ресурсів.
# # Він інтегрується з системою автентифікації (`backend.app.src.core.dependencies`)
# # для отримання інформації про поточного користувача.
# #
# # Основні компоненти:
# # - Базовий клас `Permission`: Абстрактний клас для всіх кастомних дозволів.
# # - Специфічні класи дозволів (наприклад, `IsAuthenticated`, `IsSuperuser`, `IsGroupAdmin`).
# # - `PermissionDependency`: Фабрика, що створює залежності FastAPI для перевірки
# #   набору дозволів для поточного користувача перед доступом до ендпоінту.
# #
# # Важливо: `UserModel` імпортується з `core.dependencies` і наразі є заповнювачем.

from functools import wraps
from typing import Callable, List, Optional, Any, Coroutine, Type, Union as TypingUnion
from enum import Enum # Використовується в require_roles та прикладах

from fastapi import Depends, HTTPException, status, Request

# TODO: (ВАЖЛИВО) Оновити імпорт UserModel, коли реальна модель User буде доступна в backend.app.src.models.auth.user
from backend.app.src.core.dependencies import get_current_active_user, UserModel  # UserModel тут є заповнювачем (placeholder)
from backend.app.src.core.dicts import GroupRole  # Імпорт Enum для ролей в групі (використовується в @require_roles)
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


# TODO: Розглянути імпорт реальної сесії БД (`AsyncSession`) та репозиторію/сервісу для GroupMembership,
#       коли вони будуть доступні та потрібні для дозволів, що взаємодіють з БД (напр., реальний IsGroupAdmin).
# from backend.app.src.config.database import AsyncSession, get_db
# from backend.app.src.repositories.groups.group_membership_repository import GroupMembershipRepository # Приклад шляху


class Permission:
    """
    Базовий абстрактний клас для визначення користувацьких дозволів (permissions).
    Кожен конкретний дозвіл повинен успадковувати цей клас та реалізовувати
    асинхронний метод `has_permission`.
    """

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        """
        Асинхронний метод для перевірки, чи має користувач необхідний дозвіл.

        Цей метод викликається `PermissionDependency` для кожного дозволу зі списку.

        Args:
            request (Request): Об'єкт запиту FastAPI. Надає доступ до тіла запиту,
                               заголовків, параметрів шляху тощо.
            user (UserModel): Об'єкт поточного користувача, отриманий з залежності
                              (наприклад, `get_current_active_user`). Для анонімних
                              користувачів (якщо дозволено опціональною автентифікацією)
                              може бути `None`.
            **kwargs: Додаткові аргументи, які можуть бути передані з `PermissionDependency`
                      (наприклад, `group_id` з параметрів шляху, або сесія БД).

        Returns:
            bool: `True`, якщо дозвіл надано, `False` в іншому випадку.

        Raises:
            NotImplementedError: Якщо метод не реалізований у конкретному підкласі дозволу.
        """
        # i18n: Error message for developers
        raise NotImplementedError("Метод has_permission повинен бути реалізований у підкласі дозволу.")


class IsAuthenticated(Permission):
    """Дозвіл, що надає доступ лише автентифікованим та активним користувачам."""

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # Залежність `get_current_active_user` (яка зазвичай передає `user` сюди)
        # вже гарантує, що `user` існує та є активним (`user.is_active == True`).
        # Цей клас дозволу просто підтверджує цей стан.
        # Якщо б використовувалася опціональна автентифікація (де `user` може бути `None`),
        # то тут була б явна перевірка `user is not None and user.is_active`.
        is_permitted = user is not None and hasattr(user, 'is_active') and user.is_active
        # i18n: Log message for developers
        logger.debug(
            f"IsAuthenticated: Користувач '{user.email if user else 'Анонімний'}', "
            f"активний: {user.is_active if user and hasattr(user, 'is_active') else 'N/A'}. Дозвіл: {is_permitted}")
        return is_permitted


class IsSuperuser(Permission):
    """Дозвіл, що надає доступ лише активним суперкористувачам."""

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # `get_current_active_user` (яка зазвичай передає `user`) гарантує, що `user` активний.
        # Перевіряємо, чи користувач є суперкористувачем.
        is_superuser_flag = hasattr(user, 'is_superuser') and user.is_superuser
        is_permitted = user is not None and hasattr(user, 'is_active') and user.is_active and is_superuser_flag
        # i18n: Log message for developers
        logger.debug(f"IsSuperuser: Користувач '{user.email}', суперкористувач: {is_superuser_flag}. Дозвіл: {is_permitted}")
        return is_permitted


class IsGroupAdmin(Permission):
    """
    Дозвіл, що надає доступ лише користувачам, які є адміністраторами (або власниками)
    конкретної групи. Цей дозвіл вимагає, щоб `group_id` було передано
    через `PermissionDependency` з параметрів шляху запиту.

    ВАЖЛИВО: Поточна реалізація є заповнювачем (placeholder) і потребує інтеграції
    з базою даних для реальної перевірки ролі користувача в групі.
    """

    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        # `get_current_active_user` (що зазвичай передає `user`) гарантує, що `user` активний.
        if not (user and hasattr(user, 'is_active') and user.is_active):
            # i18n: Log message for developers
            logger.warning(f"IsGroupAdmin: Спроба перевірки для неактивного або неавтентифікованого користувача.")
            return False # Додаткова перевірка, хоча має бути гарантована залежністю.

        group_id = kwargs.get("group_id") # Отримуємо group_id, переданий з PermissionDependency
        if group_id is None:
            # i18n: Log message for developers
            logger.error(
                "IsGroupAdmin: `group_id` не було надано для перевірки дозволу. "
                "Це вказує на помилку конфігурації шляху або залежності `PermissionDependency`."
            )
            # У реальному сценарії це може вказувати на помилку розробника.
            # Можна повернути False або викликати внутрішню помилку сервера (HTTP 500).
            return False

        # i18n: Log message for developers
        logger.debug(f"IsGroupAdmin: Перевірка прав адміністратора для користувача '{user.email}' (ID: {user.id}) у групі ID: {group_id}.")

        # --- TODO: (ВАЖЛИВО) Замінити логіку-заповнювач на реальну перевірку членства та ролі в групі ---
        # Ця логіка має використовувати репозиторій/сервіс для запиту до БД.
        # Потрібно отримати сесію БД (наприклад, передати її через kwargs з PermissionDependency).
        #
        # Приклад реальної логіки:
        # db_session: Optional[AsyncSession] = kwargs.get("db")
        # if not db_session:
        #     logger.error("IsGroupAdmin: Сесія БД (db) не була передана для перевірки дозволу.")
        #     return False # Або викликати HTTP 500, оскільки це помилка конфігурації.
        #
        # # Припустимо, існує сервіс або репозиторій для роботи з членством у групах
        # from backend.app.src.services.group_membership_service import GroupMembershipService # Потрібно створити
        # membership_service = GroupMembershipService(db_session)
        # user_role_in_group = await membership_service.get_user_role_in_group(user_id=user.id, group_id=group_id)
        #
        # if user_role_in_group and user_role_in_group in [GroupRole.ADMIN, GroupRole.OWNER]:
        #     logger.info(f"IsGroupAdmin: Користувач '{user.email}' є '{user_role_in_group.value}' групи {group_id}. Дозвіл надано.")
        #     return True
        # --- Кінець TODO блоку для реальної логіки ---

        # Поточна логіка-заповнювач:
        # 1. Суперкористувач завжди має доступ.
        if hasattr(user, 'is_superuser') and user.is_superuser:
            # i18n: Log message for developers
            logger.debug(
                f"IsGroupAdmin: Користувач '{user.email}' є суперкористувачем. "
                f"Надано доступ до адміністрування групи {group_id} (обхід стандартної перевірки ролі в групі).")
            return True
        # 2. Імітація: користувач з ID X є адміністратором групи X (для простоти тестування заповнювача).
        if hasattr(user, 'id') and user.id == group_id: # Дуже спрощена логіка-заповнювач!
            # i18n: Log message for developers
            logger.debug(
                f"IsGroupAdmin: Користувач ID {user.id} вважається адміністратором групи {group_id} (за логікою-заповнювачем). Дозвіл надано.")
            return True

        # i18n: Log message for developers
        logger.info(
            f"IsGroupAdmin: Користувач '{user.email}' (ID: {user.id}) не є адміністратором групи {group_id} "
            f"(за поточною логікою-заповнювачем). Дозвіл відхилено.")
        return False


class AllowAll(Permission):
    """
    Дозвіл, що завжди надає доступ (завжди повертає `True`).
    Корисний для публічних ендпоінтів або коли контроль доступу обробляється
    іншим, специфічним для ендпоінту, чином.
    Якщо цей дозвіл використовується разом із залежністю, що вимагає автентифікації
    (наприклад, `get_current_active_user`), то користувач все одно буде автентифікований.
    Для справді публічного доступу (включаючи анонімних користувачів) потрібна
    опціональна автентифікація на рівні залежності користувача.
    """

    async def has_permission(self, request: Request, user: Optional[UserModel], **kwargs: Any) -> bool:
        # i18n: Log message for developers
        logger.debug(f"AllowAll: Дозвіл надано для користувача '{user.email if user else 'Анонімний'}'.")
        return True


# --- Фабрика залежностей дозволів ---

def PermissionDependency(
        permissions: List[Type[Permission]],  # Очікуємо список класів дозволів (наприклад, [IsAuthenticated, IsGroupAdmin])
        require_all: bool = True,
        allow_superuser_override: bool = True
) -> Callable[..., Coroutine[Any, Any, UserModel]]:
    """
    Фабрика залежностей FastAPI, яка створює та повертає асинхронну функцію-залежність
    (`_permission_checker`) для перевірки набору дозволів для поточного користувача.

    Ця фабрика дозволяє гнучко комбінувати різні класи дозволів для захисту ендпоінтів.

    Args:
        permissions (List[Type[Permission]]): Список класів дозволів (не екземплярів!),
                                              які потрібно перевірити для доступу.
        require_all (bool): Якщо `True` (за замовчуванням), користувач повинен мати всі
                            вказані дозволи зі списку `permissions`.
                            Якщо `False`, достатньо мати хоча б один дозвіл зі списку.
        allow_superuser_override (bool): Якщо `True` (за замовчуванням), суперкористувач
                                         автоматично проходить усі перевірки дозволів,
                                         незалежно від списку `permissions`.

    Returns:
        Callable: Асинхронна функція-залежність, готова для використання з `Depends()` в FastAPI.
                  Ця функція повертає об'єкт користувача, якщо всі перевірки пройдені,
                  або викликає `HTTPException` (403 Forbidden) у разі відмови в доступі.
    """
    # Створюємо екземпляри класів дозволів один раз при ініціалізації залежності.
    perm_instances = [perm_class() for perm_class in permissions]

    async def _permission_checker(
            request: Request, # Об'єкт запиту FastAPI, надається автоматично
            user: UserModel = Depends(get_current_active_user) # Залежність для отримання поточного активного користувача
            # TODO: Розглянути можливість опціональної автентифікації, якщо деякі дозволи
            #       мають працювати для анонімних користувачів (наприклад, AllowAll).
            #       Це потребуватиме створення `get_current_user_optional`, який не викликає помилку, якщо токен відсутній.
            # user: Optional[UserModel] = Depends(get_current_user_optional)
            #
            # TODO: Розглянути передачу сесії БД (`db: AsyncSession = Depends(get_db)`) сюди,
            #       якщо класи дозволів (наприклад, реальний `IsGroupAdmin`) потребуватимуть
            #       доступу до бази даних для перевірки. Потім `db` можна передавати в `perm_instance.has_permission`.
    ) -> UserModel: # Повертає об'єкт користувача, якщо доступ дозволено.
        # `get_current_active_user` вже викликає HTTPException(401 або 403), якщо користувач
        # не автентифікований або неактивний, тому тут ми вже маємо активного користувача.

        # Обхід перевірок для суперкористувача, якщо опція `allow_superuser_override` увімкнена.
        if allow_superuser_override and hasattr(user, 'is_superuser') and user.is_superuser:
            # i18n: Log message for developers
            logger.debug(f"Дозвіл автоматично надано суперкористувачу '{user.email}' (allow_superuser_override=True).")
            return user

        # Вилучення параметрів шляху з запиту (наприклад, `group_id`) для передачі в `has_permission`.
        path_params = request.path_params.copy()  # Копіюємо, щоб уникнути модифікації оригінального об'єкта.

        results = [] # Список результатів перевірки кожного дозволу (True/False)
        for perm_instance in perm_instances:
            kwargs_for_perm = {} # Аргументи для передачі в has_permission конкретного дозволу

            # Спеціальна обробка для IsGroupAdmin для передачі `group_id` з параметрів шляху.
            # Це приклад, як можна передавати контекстні дані до класів дозволів.
            if isinstance(perm_instance, IsGroupAdmin) and 'group_id' in path_params:
                try:
                    kwargs_for_perm['group_id'] = int(path_params['group_id'])
                except ValueError:
                    # i18n: Log message for developers
                    logger.warning(
                        f"Недійсний формат group_id ('{path_params['group_id']}') у шляху для перевірки IsGroupAdmin.",
                        exc_info=True
                    )
                    # TODO i18n: Translatable user-facing error message. "Недійсний формат ID групи у шляху."
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Недійсний формат ID групи у шляху.")

            # TODO: Якщо класи дозволів потребують сесію БД, її потрібно передати сюди:
            # kwargs_for_perm['db'] = db_session # `db_session` має бути отримано через Depends(get_db) вище.

            has_perm = await perm_instance.has_permission(request, user, **kwargs_for_perm)
            results.append(has_perm)

        # Якщо список `permissions` був порожній, а `allow_superuser_override` вимкнено,
        # то доступ за замовчуванням заборонено (бо немає жодного дозволу, що міг би його надати).
        # Цей випадок малоймовірний при правильному використанні, але варто обробити.
        if not permissions: # Якщо список permissions порожній (немає чого перевіряти)
            if not (allow_superuser_override and hasattr(user, 'is_superuser') and user.is_superuser):
                 # i18n: Log message for developers
                logger.warning(f"Доступ для користувача '{user.email}' заборонено: список дозволів порожній, і користувач не є суперкористувачем з правом обходу.")
                # TODO i18n: Translatable user-facing error message. "Доступ заборонено: не налаштовано правила доступу."
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ заборонено: не налаштовано правила доступу.")
            # Якщо ж суперкористувач з правом обходу, він вже повернувся раніше.

        # Визначення остаточного рішення на основі результатів та параметра `require_all`.
        final_decision = all(results) if require_all else any(results)

        if not final_decision:
            # i18n: Log message for developers
            logger.warning(
                f"Користувачу '{user.email}' відмовлено в доступі. "
                f"Результати перевірок дозволів: {results} (вимагалося {'ВСІ' if require_all else 'БУДЬ-ЯКИЙ'} з них)."
            )
            # TODO i18n: Translatable user-facing error message. "У вас недостатньо прав для виконання цієї дії."
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостатньо прав для виконання цієї дії."
            )

        # i18n: Log message for developers
        logger.debug(f"Користувачу '{user.email}' надано доступ. Результати перевірок: {results}.")
        return user # Повертаємо об'єкт користувача, якщо всі перевірки пройдені.

    return _permission_checker


# --- TODO: Оцінити доцільність використання декоратора @require_roles для FastAPI ---
# Хоча такий декоратор може бути корисним в інших фреймворках (наприклад, Flask з кастомною автентифікацією),
# для FastAPI підхід з класами дозволів та фабрикою `PermissionDependency` зазвичай є більш гнучким,
# краще інтегрується з системою залежностей FastAPI (що дозволяє легше тестувати та керувати залежностями,
# такими як сесія БД), та надає більше контексту (об'єкт `request`) для перевірки дозволів.
# Декоратори, що модифікують сигнатуру функції або покладаються на конкретні імена аргументів,
# можуть бути менш зручними в FastAPI.
# Залишено для можливого обговорення або для специфічних випадків, де він може бути доречним.
def require_roles(allowed_roles: List[TypingUnion[str, Enum]]):
    """
    Декоратор для обмеження доступу ендпоінту користувачам з певними ролями.
    Припускає, що об'єкт `user`, переданий до обгорнутої функції, має атрибут `roles`,
    який є списком рядків або членів Enum, що представляють ролі користувача.

    УВАГА: Цей підхід менш типовий для FastAPI порівняно з використанням `Depends` та класів дозволів.
    Розгляньте використання `PermissionDependency` з кастомним дозволом для перевірки ролей.

    Args:
        allowed_roles (List[Union[str, Enum]]): Список рядків або членів Enum, що представляють
                                                 дозволені ролі для доступу.
    """

    def decorator(func: Callable[..., Any]): # func - це асинхронний обробник шляху FastAPI
        @wraps(func) # Зберігає метадані оригінальної функції (назва, docstring тощо)
        async def wrapper(*args: Any, **kwargs: Any):
            # У FastAPI 'user' зазвичай отримується через Depends(get_current_active_user)
            # і передається як іменований аргумент функції обробника шляху.
            # Спробуємо знайти 'user' серед іменованих аргументів.
            user: Optional[UserModel] = kwargs.get('user')
            # Якщо 'user' не знайдено серед іменованих, спробуємо знайти серед позиційних (менш надійно).
            if user is None:
                user = next((arg for arg in args if isinstance(arg, UserModel)), None)

            if not user: # Якщо користувача не знайдено або він None (для опціональної автентифікації)
                # i18n: Log message for developers
                logger.warning("@require_roles: Користувача не знайдено в аргументах функції або він не автентифікований. Доступ заборонено.")
                # TODO i18n: Translatable user-facing error message. "Доступ заборонено: користувача не автентифіковано."
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, # 401, оскільки це проблема автентифікації
                                    detail="Доступ заборонено: користувача не автентифіковано.")

            if not hasattr(user, 'roles'): # Перевірка наявності атрибута 'roles'
                # i18n: Log message for developers
                logger.error(f"@require_roles: Об'єкт користувача '{user.email}' не має атрибута 'roles'. Помилка конфігурації.")
                # TODO i18n: Translatable user-facing error message. "Помилка конфігурації ролей користувача."
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Помилка конфігурації ролей користувача.")

            user_roles_attr = getattr(user, 'roles')
            if not isinstance(user_roles_attr, list): # Перевірка, чи 'roles' є списком
                # i18n: Log message for developers
                logger.error(
                    f"@require_roles: Атрибут 'roles' користувача '{user.email}' не є списком (тип: {type(user_roles_attr)})."
                )
                # TODO i18n: Translatable user-facing error message. "Неправильний формат ролей користувача."
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Неправильний формат ролей користувача.")

            # Перетворення значень Enum на рядки для порівняння, якщо потрібно
            allowed_role_values = [role.value if isinstance(role, Enum) else str(role) for role in allowed_roles]
            user_role_values = [user_role.value if isinstance(user_role, Enum) else str(user_role) for user_role in user_roles_attr]

            # Перевірка, чи має користувач хоча б одну з дозволених ролей
            if not any(user_r_val in allowed_role_values for user_r_val in user_role_values):
                # i18n: Log message for developers
                logger.warning(
                    f"@require_roles: Користувач '{user.email}' з ролями {user_role_values} "
                    f"не має жодної з дозволених ролей: {allowed_role_values}. Доступ заборонено."
                )
                # TODO i18n: Translatable user-facing error message (possibly with placeholder for roles)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Для доступу потрібна одна з наступних ролей: {', '.join(allowed_role_values)}")

            # i18n: Log message for developers
            logger.debug(
                f"@require_roles: Користувач '{user.email}' з ролями {user_role_values} "
                f"має доступ (дозволені ролі: {allowed_role_values})."
            )
            return await func(*args, **kwargs) # Виклик оригінальної функції обробника шляху

        return wrapper
    return decorator


# Блок для демонстрації та базового тестування при прямому запуску модуля.
if __name__ == "__main__":
    # Налаштування логування для тестування (якщо воно ще не налаштоване глобально)
    try:
        from backend.app.src.config.logging import setup_logging
        from backend.app.src.config.settings import settings # Потрібно для шляхів логів
        from pathlib import Path
        if settings.LOG_TO_FILE: # Налаштовуємо логування у файл, якщо вказано
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging() # Стандартне логування в консоль
        logger.info("Логування налаштовано для тестування permissions.py.")
    except ImportError:
        import logging as base_logging # Використовуємо стандартний logging, якщо кастомний недоступний
        base_logging.basicConfig(level=logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів permissions.py.")

    logger.info("--- Демонстрація Модуля Дозволів (`core.permissions`) ---")
    logger.info("Цей модуль визначає класи дозволів та фабрику залежностей для FastAPI.")

    # Створення макетів об'єктів користувачів для демонстрації (використовуємо UserModel-заповнювач)
    # TODO: Замінити UserModel на реальну модель, коли вона буде доступна.
    active_user_instance = UserModel(id=1, email="user@example.com", is_active=True)
    # Додаємо атрибут 'roles' для тестування декоратора @require_roles
    setattr(active_user_instance, 'roles', [GroupRole.MEMBER.value, "editor"]) # Приклад з Enum та рядком

    inactive_user_instance = UserModel(id=2, email="inactive@example.com", is_active=False)
    setattr(inactive_user_instance, 'roles', [GroupRole.MEMBER.value])

    superuser_instance = UserModel(id=3, email="super@example.com", is_active=True, is_superuser=True)
    setattr(superuser_instance, 'roles', [SystemUserRole.SUPERUSER.value, GroupRole.ADMIN.value]) # Приклад з Enum

    # Користувач для тестування IsGroupAdmin; використовується логіка-заповнювач: користувач ID 4 є адміном групи 4
    group_admin_user_instance = UserModel(id=4, email="admin_g4@example.com", is_active=True, is_superuser=False)
    setattr(group_admin_user_instance, 'roles', [GroupRole.ADMIN.value])


    # Створення макетів об'єктів Request для тестування (для вилучення path_params в IsGroupAdmin)
    mock_request_no_params = Request(scope={"type": "http", "method": "GET", "path": "/items", "path_params": {}})
    mock_request_group1_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/1/items", "path_params": {"group_id": "1"}})
    mock_request_group4_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/4/items", "path_params": {"group_id": "4"}})
    mock_request_invalid_group_path = Request(
        scope={"type": "http", "method": "GET", "path": "/groups/abc/items", "path_params": {"group_id": "abc"}})


    async def run_permission_check_demo(perm_class: Type[Permission], user_instance: Optional[UserModel],
                                        request_obj: Request, desc: str, **perm_kwargs):
        """Допоміжна функція для демонстрації перевірки дозволів та виводу результатів."""
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
                    f"Тест '{desc}' ({perm_name}): Некоректний group_id '{request_obj.path_params['group_id']}' для користувача '{user_email}'. Пропускаємо.")
                return

        logger.info(f"\nТестування '{desc}' ({perm_name}): Користувач '{user_email}', шлях '{request_obj.url.path}', дод. kwargs: {final_kwargs}")
        try:
            has_perm = await perm.has_permission(request_obj, user_instance, **final_kwargs)
            logger.info(
                f"Результат: Дозвіл {'НАДАНО' if has_perm else 'ВІДМОВЛЕНО'}")
        except Exception as e:
            logger.error(f"Помилка під час перевірки дозволу '{desc}' ({perm_name}) для користувача '{user_email}': {e}",
                         exc_info=True)


    import asyncio # Потрібно для asyncio.run()

    async def main_test_permissions():
        """Основна асинхронна функція для запуску демонстрації дозволів."""
        logger.info("\n--- Тестування Класів Дозволів ---")

        await run_permission_check_demo(IsAuthenticated, active_user_instance, mock_request_no_params, "Активний користувач")
        await run_permission_check_demo(IsAuthenticated, inactive_user_instance, mock_request_no_params, "Неактивний користувач")

        await run_permission_check_demo(IsSuperuser, active_user_instance, mock_request_no_params, "Звичайний активний користувач")
        await run_permission_check_demo(IsSuperuser, superuser_instance, mock_request_no_params, "Суперкористувач")

        logger.info("\nТестування IsGroupAdmin (використовується логіка-заповнювач):")
        await run_permission_check_demo(IsGroupAdmin, group_admin_user_instance, mock_request_group4_path, "Адмін групи 4 для групи 4")
        await run_permission_check_demo(IsGroupAdmin, group_admin_user_instance, mock_request_group1_path, "Адмін групи 4 для групи 1")
        await run_permission_check_demo(IsGroupAdmin, superuser_instance, mock_request_group1_path, "Суперкористувач для групи 1")
        await run_permission_check_demo(IsGroupAdmin, active_user_instance, mock_request_group1_path, "Звичайний користувач для групи 1")
        await run_permission_check_demo(IsGroupAdmin, active_user_instance, mock_request_invalid_group_path, "Невалідний group_id")
        await run_permission_check_demo(IsGroupAdmin, active_user_instance, mock_request_no_params, "Без group_id (помилка конфігурації)")


        await run_permission_check_demo(AllowAll, active_user_instance, mock_request_no_params, "Активний користувач")
        await run_permission_check_demo(AllowAll, None, mock_request_no_params, "Анонімний користувач")

        logger.info("\n--- Тестування Декоратора @require_roles (концептуальне) ---")
        logger.info("Примітка: Декоратор тестується з прямими викликами, передаючи 'user' як іменований аргумент.")

        @require_roles([GroupRole.ADMIN, SystemUserRole.SUPERUSER])
        async def example_admin_or_superuser_required_func(user: UserModel, **kwargs): # Додано **kwargs для гнучкості
            logger.info(f"Користувач '{user.email}' успішно виконав дію, що вимагає ролі АДМІН або СУПЕРКОРИСТУВАЧ.")

        @require_roles([GroupRole.MEMBER])
        async def example_member_required_func(user: UserModel, **kwargs):
            logger.info(f"Користувач '{user.email}' успішно виконав дію, що вимагає ролі УЧАСНИК.")

        logger.info("\nТест @require_roles (для admin_or_superuser_required_func):")
        try: await example_admin_or_superuser_required_func(user=superuser_instance)
        except HTTPException as e: logger.error(f"  Superuser: {e.detail} (ПОМИЛКА, очікувався успіх)")
        try: await example_admin_or_superuser_required_func(user=group_admin_user_instance) # Має роль GroupRole.ADMIN
        except HTTPException as e: logger.error(f"  GroupAdmin: {e.detail} (ПОМИЛКА, очікувався успіх)")
        try: await example_admin_or_superuser_required_func(user=active_user_instance) # Має GroupRole.MEMBER
        except HTTPException as e: logger.warning(f"  ActiveUser (member): {e.detail} (ОЧІКУВАНА ВІДМОВА)")

        logger.info("\nТест @require_roles (для member_required_func):")
        try: await example_member_required_func(user=active_user_instance)
        except HTTPException as e: logger.error(f"  ActiveUser (member): {e.detail} (ПОМИЛКА, очікувався успіх)")

        user_without_any_roles = UserModel(id=5, email="noroles@example.com", is_active=True)
        setattr(user_without_any_roles, 'roles', []) # Атрибут roles є, але список порожній
        try: await example_member_required_func(user=user_without_any_roles)
        except HTTPException as e: logger.warning(f"  User with empty roles list: {e.detail} (ОЧІКУВАНА ВІДМОВА)")

        user_with_no_roles_attr = UserModel(id=6, email="no_roles_attr@example.com", is_active=True)
        # Атрибут 'roles' навмисно не встановлено
        try: await example_member_required_func(user=user_with_no_roles_attr)
        except HTTPException as e: logger.warning(f"  User with no 'roles' attribute: {e.detail} (ОЧІКУВАНА ВІДМОВА - помилка конфігурації)")


        logger.info("\nДемонстрація дозволів завершена. Перевірте вивід логів для деталей.")
        logger.info("Пам'ятайте, що `PermissionDependency` та класи дозволів зазвичай використовуються "
                    "в `Depends()` в ендпоінтах FastAPI для автоматичної перевірки.")


    asyncio.run(main_test_permissions())

[end of backend/app/src/core/permissions.py]
