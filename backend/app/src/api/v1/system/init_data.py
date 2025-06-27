# backend/app/src/api/v1/system/init_data.py
# -*- coding: utf-8 -*-
"""
Ендпоінт для запуску ініціалізації початкових даних системи.

Цей модуль надає API ендпоінт, який дозволяє адміністратору системи
(зазвичай суперкористувачу) запустити процес створення/оновлення
початкових даних, таких як:
- Заповнення довідників (статуси, ролі, типи тощо).
- Створення системних користувачів (superadmin, боти).
- Інші необхідні початкові налаштування.

Цей ендпоінт має бути захищений відповідними правами доступу.
"""

from typing import Dict, Any, Optional # Додано Optional
from fastapi import APIRouter, Depends, HTTPException, status
# sqlalchemy.ext.asyncio.AsyncSession більше не потрібен тут напряму
from pydantic import BaseModel # Для схеми відповіді

from backend.app.src.config.logging import get_logger
from backend.app.src.services.system.initialization_service import InitializationService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
# UserModel потрібен для type hinting current_user
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Схема відповіді для ендпоінтів ініціалізації
class InitializationResponseSchema(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


@router.post(
    "/initialize-data",
    response_model=InitializationResponseSchema,
    tags=["System", "Initialization"],
    summary="Запуск ініціалізації початкових даних",
    description="""
    Ініціалізує базові дані системи, такі як довідники та системні користувачі.
    **Потребує прав суперкористувача.**
    """,
    # Залежність CurrentSuperuser вже перевіряє права та активність користувача
)
async def trigger_initialize_data(
    db_session: DBSession = Depends(), # Тепер просто Depends()
    current_user: UserModel = Depends(CurrentSuperuser) # Використовуємо UserModel для type hint
):
    """
    Запускає процес ініціалізації початкових даних системи.
    """
    logger.info(f"Запит на ініціалізацію даних отримано від користувача: {current_user.email}")

    init_service = InitializationService(db_session)
    try:
        # Припускаємо, що сервіс повертає словник, який можна передати в details
        result_details = await init_service.run_full_initialization()
        logger.info(f"Ініціалізація даних успішно завершена: {result_details}")
        return InitializationResponseSchema(
            status="success",
            message="Повна ініціалізація системи успішно завершена.",
            details=result_details
        )
    except Exception as e:
        logger.error(f"Помилка під час ініціалізації даних: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка сервера під час ініціалізації даних: {str(e)}"
        )

@router.post(
    "/initialize-dictionaries",
    response_model=InitializationResponseSchema,
    tags=["System", "Initialization"],
    summary="Запуск ініціалізації довідників",
    description="""
    Ініціалізує/оновлює системні довідники.
    **Потребує прав суперкористувача.**
    """,
)
async def trigger_initialize_dictionaries(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Запускає процес ініціалізації лише довідників.
    """
    logger.info(f"Запит на ініціалізацію довідників отримано від користувача: {current_user.email}.")
    init_service = InitializationService(db_session)
    try:
        result_details = await init_service.initialize_dictionaries()
        logger.info(f"Ініціалізація довідників успішно завершена: {result_details}")
        return InitializationResponseSchema(
            status="success",
            message="Ініціалізація довідників успішно завершена.",
            details=result_details
        )
    except Exception as e:
        logger.error(f"Помилка під час ініціалізації довідників: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка сервера під час ініціалізації довідників: {str(e)}"
        )

# Роутер буде підключений в backend/app/src/api/v1/system/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
