# backend/app/src/api/v1/system/settings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління загальними налаштуваннями системи API v1.

Ці ендпоінти призначені для суперкористувачів та дозволяють
переглядати та модифікувати глобальні параметри системи.
"""

import asyncio # Додано для FakeSystemSettingsService
import logging
from typing import Dict, Any, List, Optional # List, Optional для Pydantic моделей

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl # HttpUrl для валідації URL

# Залежності API (для автентифікації/авторизації)
# У реальному проекті: from app.src.api.dependencies import get_current_active_superuser
# Для прикладу, імітуємо цю залежність, якщо вона ще не повністю функціональна,
# або для тестування цього модуля ізольовано.
# Імпортуємо заглушку _fake_user_service, щоб get_current_active_superuser_stub міг її використати.
from app.src.api.dependencies import _fake_user_service

# Сервіс для роботи з налаштуваннями (буде реалізовано пізніше в src/services/)
# from app.src.services.system.settings_service import SystemSettingsService

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic моделі для налаштувань ---

class MaintenanceModeSettings(BaseModel):
    enabled: bool = Field(False, description="Чи ввімкнено режим технічного обслуговування.")
    message: Optional[str] = Field(
        None,
        description="Повідомлення для користувачів під час тех. обслуговування.",
        example="Система на короткостроковому обслуговуванні. Спробуйте пізніше."
    )

class NotificationSettings(BaseModel):
    default_email_sender: Optional[str] = Field(
        None,
        description="Email адреса відправника за замовчуванням для системних сповіщень.",
        example="noreply@kudos.example.com"
    )
    disable_all_sms: bool = Field(False, description="Повністю вимкнути відправку SMS сповіщень глобально.")
    # Тут можуть бути інші налаштування, наприклад, для різних типів сповіщень

class ExternalAPISettings(BaseModel):
    # Приклад, якщо система інтегрується з якимось зовнішнім сервісом
    some_external_service_url: Optional[HttpUrl] = Field(
        None,
        description="URL для інтеграції з зовнішнім сервісом XYZ."
    )
    some_external_service_api_key: Optional[str] = Field(
        None,
        description="API ключ для зовнішнього сервісу XYZ (зберігати обережно!)."
    )
    # Додайте інші поля за потребою

class SystemSettingsSchema(BaseModel):
    """Схема для представлення всіх системних налаштувань, доступних через API."""
    site_name: str = Field(
        ..., # Означає, що поле обов'язкове
        description="Публічна назва сайту/додатку.",
        example="Kudos Platform"
    )
    support_email: Optional[str] = Field(
        None,
        description="Контактний email служби підтримки для користувачів.",
        example="support@kudos.example.com"
    )
    maintenance_mode: MaintenanceModeSettings = Field(
        default_factory=MaintenanceModeSettings,
        description="Налаштування режиму технічного обслуговування."
    )
    notification_settings: NotificationSettings = Field(
        default_factory=NotificationSettings,
        description="Загальні налаштування сповіщень."
    )
    external_api_config: Optional[ExternalAPISettings] = Field( # Змінено назву для уникнення конфлікту
        None,
        description="Налаштування для інтеграції з зовнішніми API."
    )
    allowed_cors_origins: List[str] = Field(
        default_factory=list,
        description="Список дозволених CORS origins. Наприклад, ['https://myfrontend.example.com'].",
        example=["http://localhost:3000", "https://prod.kudos.example.com"]
    )
    # Можна додати інші глобальні налаштування тут:
    # default_user_role: Optional[str] = Field("user", description="Роль за замовчуванням для нових користувачів")
    # max_session_lifetime_hours: Optional[int] = Field(24*7, description="Максимальний час життя сесії в годинах")


# --- Заглушка для сервісу налаштувань ---
# У реальній системі це буде взаємодія з БД (наприклад, таблиця `system_configurations`)
# або з конфігураційним файлом/сервісом (наприклад, Consul, etcd, або змінні середовища).
_current_system_settings_instance = SystemSettingsSchema( # Використовуємо інше ім'я змінної
    site_name="Kudos Система (За замовчуванням)",
    support_email="admin@kudos.example.com",
    maintenance_mode=MaintenanceModeSettings(enabled=False, message=""),
    notification_settings=NotificationSettings(default_email_sender="noreply@kudos.example.com", disable_all_sms=False),
    external_api_config=None, # За замовчуванням немає
    allowed_cors_origins=["http://localhost:8000", "http://127.0.0.1:8000"] # Приклад для локальної розробки
)

class FakeSystemSettingsService:
    """Імітує сервіс для роботи з системними налаштуваннями."""
    async def get_settings(self) -> SystemSettingsSchema:
        logger.debug("FakeSystemSettingsService: Повернення поточних системних налаштувань (заглушка).")
        await asyncio.sleep(0.01) # Імітація IO операції
        return _current_system_settings_instance

    async def update_settings(self, new_settings_payload: SystemSettingsSchema) -> SystemSettingsSchema:
        global _current_system_settings_instance # Модифікуємо глобальну змінну для імітації збереження
        logger.info(
            f"FakeSystemSettingsService: Оновлення системних налаштувань (заглушка). "
            f"Нові дані: {new_settings_payload.model_dump_json(indent=2, exclude_unset=True)}"
        )
        # У реальній системі тут буде валідація, можливо, часткове оновлення,
        # збереження в БД або конфігураційний файл, та, можливо, сповіщення інших частин системи про зміни.
        # Наприклад, якщо змінився `maintenance_mode`, інші сервіси мають це врахувати.

        # Для простої заглушки - повна заміна об'єкта налаштувань.
        _current_system_settings_instance = new_settings_payload.model_copy(deep=True)
        await asyncio.sleep(0.01) # Імітація IO операції
        logger.info("FakeSystemSettingsService: Системні налаштування 'збережено'.")
        return _current_system_settings_instance

_fake_settings_service_instance = FakeSystemSettingsService() # Створюємо екземпляр сервісу-заглушки

# --- Імітація залежності get_current_active_superuser ---
# Ця залежність має бути в api.dependencies.py. Для локального тестування цього модуля,
# якщо залежності ще не повністю налаштовані, можна тимчасово імітувати її тут.
# ВАЖЛИВО: У фінальній версії ця заглушка має бути видалена, а використовуватися має
# залежність з app.src.api.dependencies.
async def get_current_active_superuser_stub(token: str = "valid_superuser_token") -> Dict[str, Any]:
    """
    Заглушка для залежності, що перевіряє права суперкористувача.
    Використовує _fake_user_service з app.src.api.dependencies.
    """
    # Припускаємо, що токен "valid_superuser_token" відповідає суперюзеру в FakeUserService
    # Це лише імітація отримання токена; реально він прийде з Depends(OAUTH2_SCHEME)
    # і буде оброблений в get_current_active_superuser в dependencies.py
    user = await _fake_user_service.get_user_by_id("superuser_id")
    if not user or not user.get("is_active") or not user.get("is_superuser"):
        logger.warning(f"Заглушка: Спроба доступу без прав суперкористувача (токен: {token[:10]}...).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права суперкористувача (локальна заглушка)."
        )
    logger.debug(f"Заглушка: Користувач '{user.get('username')}' авторизований як суперюзер.")
    return user


# --- Ендпоінти ---

@router.get(
    "", # Шлях буде /api/v1/system/settings (якщо system_router має префікс /system, а v1_router /v1)
    response_model=SystemSettingsSchema,
    summary="Отримати поточні системні налаштування",
    response_description="Повертає об'єкт з усіма поточними системними налаштуваннями.",
    dependencies=[Depends(get_current_active_superuser_stub)] # Захист ендпоінта суперюзером
)
async def get_system_settings(
    # У реальному проекті: settings_service: SystemSettingsService = Depends(get_settings_service)
):
    """
    Отримує всі поточні системні налаштування.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Запит на отримання системних налаштувань (користувач-суперюзер).")
    # settings = await settings_service.get_settings() # Реальний виклик
    settings = await _fake_settings_service_instance.get_settings() # Використання заглушки
    return settings

@router.put(
    "",
    response_model=SystemSettingsSchema,
    summary="Оновити системні налаштування",
    response_description="Повертає повний об'єкт оновлених системних налаштувань.",
    dependencies=[Depends(get_current_active_superuser_stub)] # Захист ендпоінта
)
async def update_system_settings(
    settings_update_payload: SystemSettingsSchema, # Дані для оновлення надходять у тілі запиту
    # current_super_user: Dict[str, Any] = Depends(get_current_active_superuser_stub), # Для логування, хто змінив
    # У реальному проекті: settings_service: SystemSettingsService = Depends(get_settings_service)
):
    """
    Оновлює (повністю замінює) системні налаштування.
    Наданий об'єкт `settings_update_payload` повністю замінює поточні налаштування.
    Для часткового оновлення слід використовувати метод PATCH (не реалізовано в цій заглушці).
    Доступно тільки суперкористувачам.
    """
    # user_who_updated = current_super_user.get("username", "unknown_superuser")
    # logger.info(f"Суперкористувач '{user_who_updated}' оновлює системні налаштування.")
    logger.info(f"Отримано запит на оновлення системних налаштувань. Нові дані: {settings_update_payload.model_dump(exclude_unset=True, indent=2)}")

    # updated_settings = await settings_service.update_settings(settings_update_payload) # Реальний виклик
    updated_settings = await _fake_settings_service_instance.update_settings(settings_update_payload) # Використання заглушки

    logger.info("Системні налаштування успішно оновлено.")
    return updated_settings

# Примітка: PATCH метод для часткового оновлення налаштувань може бути доданий пізніше.
# Він вимагатиме більш складної логіки для злиття полів об'єкта налаштувань,
# особливо для вкладених моделей. FastAPI підтримує це через `exclude_unset=True` при створенні моделі з payload.

# Коментар для розробника:
# Не забути оновити `backend/app/src/api/v1/system/__init__.py`, щоб підключити цей `router`.
# Наприклад, додати в __init__.py:
#
# from .settings import router as settings_router
# system_router.include_router(settings_router, prefix="/settings", tags=["V1 System Settings"])

logger.info("Модуль API v1 System Settings (`settings.py`) завантажено.")
