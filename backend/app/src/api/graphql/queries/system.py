# backend/app/src/api/graphql/queries/system.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з системною інформацією.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів, що повертаються цими запитами
from backend.app.src.api.graphql.types.system import SystemSettingType, SystemHealthType
# TODO: Імпортувати сервіси, що надають дані
# from backend.app.src.services.system.system_settings_service import SystemSettingsService
# from backend.app.src.services.system.health_service import HealthService
# from backend.app.src.core.dependencies import get_current_superuser # Для захисту запитів

@strawberry.type
class SystemQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з системою.
    Цей клас буде успадкований кореневим типом Query.
    """

    @strawberry.field(description="Отримати список всіх системних налаштувань (потребує прав супер-адміністратора).")
    async def system_settings(self, info: strawberry.Info) -> List[SystemSettingType]:
        """
        Повертає список всіх системних налаштувань.
        Доступно тільки для супер-адміністраторів.
        """
        # context = info.context
        # TODO: Перевірка прав доступу (наприклад, через context.current_user)
        # if not context.current_user or not context.current_user.is_superuser:
        #     raise Exception("Доступ заборонено: потрібні права супер-адміністратора.")
        #
        # settings_service = SystemSettingsService(context.db_session)
        # settings_models = await settings_service.get_all_settings()
        # return [SystemSettingType.from_orm(s) for s in settings_models] # Приклад конвертації

        # Заглушка
        return [
            SystemSettingType(name="site_name", value="Bossy System", description="Назва сайту", updated_at=strawberry.UNSET),
            SystemSettingType(name="maintenance_mode", value=False, description="Режим обслуговування", updated_at=strawberry.UNSET)
        ]

    @strawberry.field(description="Отримати конкретне системне налаштування за його назвою (потребує прав супер-адміністратора).")
    async def system_setting_by_name(self, info: strawberry.Info, name: str) -> Optional[SystemSettingType]:
        """
        Повертає системне налаштування за його унікальною назвою.
        Доступно тільки для супер-адміністраторів.
        """
        # context = info.context
        # TODO: Перевірка прав
        # settings_service = SystemSettingsService(context.db_session)
        # setting_model = await settings_service.get_setting_by_name(name)
        # if not setting_model:
        #     return None
        # return SystemSettingType.from_orm(setting_model)

        # Заглушка
        if name == "site_name":
            return SystemSettingType(name="site_name", value="Bossy System", description="Назва сайту", updated_at=strawberry.UNSET)
        return None

    @strawberry.field(description="Отримати поточний стан здоров'я системи та її компонентів.")
    async def system_health(self, info: strawberry.Info) -> SystemHealthType:
        """
        Повертає інформацію про стан API, бази даних та інших критичних компонентів.
        """
        # context = info.context
        # health_service = HealthService(context.db_session) # Може також перевіряти Redis, Celery
        # health_data = await health_service.check_full_health() # Сервіс повертає дані, готові для SystemHealthType
        # return SystemHealthType(**health_data) # Або SystemHealthType.from_pydantic(health_data_schema)

        # Заглушка
        from datetime import datetime
        return SystemHealthType(
            overall_status="OK",
            api_status=strawberry.UNSET, # SystemHealthType повинен мати резолвери або конкретні типи
            database_status=strawberry.UNSET,
            checked_at=datetime.utcnow()
        )
        # TODO: Для api_status та database_status потрібні конкретні екземпляри HealthStatusType
        # або реалізація їх як полів з резолверами всередині SystemHealthType.
        # Наприклад, SystemHealthType може мати поля:
        # @strawberry.field
        # async def api_status(self, info: strawberry.Info) -> HealthStatusType: ...

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "SystemQueries",
]
