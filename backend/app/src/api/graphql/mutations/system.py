# backend/app/src/api/graphql/mutations/system.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з системними налаштуваннями та операціями.
"""

import strawberry
from typing import Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.system import SystemSettingType, SystemSettingUpdateInput

# TODO: Імпортувати сервіси
# from backend.app.src.services.system.system_settings_service import SystemSettingsService
# from backend.app.src.services.system.initialization_service import InitializationService
# from backend.app.src.core.dependencies import get_current_superuser

@strawberry.type
class SystemMutations:
    """
    Клас, що групує GraphQL мутації для системних операцій.
    Доступно тільки для супер-адміністраторів.
    """

    @strawberry.mutation(description="Оновити системне налаштування.")
    async def update_system_setting(
        self, info: strawberry.Info,
        name: str = strawberry.field(description="Назва (ключ) налаштування для оновлення."),
        input: SystemSettingUpdateInput = strawberry.field(description="Нове значення налаштування.")
    ) -> Optional[SystemSettingType]:
        """
        Оновлює значення вказаного системного налаштування.
        Потребує прав супер-адміністратора.
        """
        # context = info.context
        # current_admin = context.current_user
        # if not current_admin or not current_admin.is_superuser:
        #     raise Exception("Доступ заборонено: потрібні права супер-адміністратора.")
        #
        # settings_service = SystemSettingsService(context.db_session)
        # # Сервіс приймає назву налаштування та нове значення (з input.value)
        # updated_setting_model = await settings_service.update_setting_graphql(
        #     setting_name=name,
        #     new_value=input.value # input.value - це strawberry.JSON
        # )
        # return SystemSettingType.from_orm(updated_setting_model) if updated_setting_model else None
        raise NotImplementedError("Оновлення системного налаштування ще не реалізовано.")

    @strawberry.mutation(description="Запустити ініціалізацію початкових даних системи.")
    async def initialize_system_data(self, info: strawberry.Info) -> bool: # Або повернути більш детальну відповідь
        """
        Запускає процес створення/оновлення початкових даних системи
        (довідники, системні користувачі тощо).
        Потребує прав супер-адміністратора. Повертає True у разі успішного запуску.
        """
        # context = info.context
        # current_admin = context.current_user
        # if not current_admin or not current_admin.is_superuser:
        #     raise Exception("Доступ заборонено: потрібні права супер-адміністратора.")
        #
        # initialization_service = InitializationService(context.db_session)
        # await initialization_service.run_full_initialization() # Або специфічний метод для GraphQL
        # # TODO: Додати логування
        # return True
        raise NotImplementedError("Ініціалізація системних даних ще не реалізована.")

    # TODO: Додати інші системні мутації, якщо потрібно
    # Наприклад, запуск резервного копіювання, очищення кешу тощо.

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "SystemMutations",
]
