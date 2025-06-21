# backend/app/src/api/router.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Головний агрегатор API роутерів для різних версій API.

Цей модуль визначає `api_router`, який є екземпляром `APIRouter` від FastAPI.
Він призначений для підключення всіх версійних роутерів (наприклад, v1, v2)
та будь-яких загальних API ендпоінтів, які не належать до конкретної версії.

`api_router` потім підключається до основного екземпляру FastAPI додатка в `main.py`.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from fastapi import APIRouter, status

from backend.app.src.api.v1 import v1_router
from backend.app.src.api.external import external_api_router
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


api_router = APIRouter(
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": _("api_router.responses.400")},
        status.HTTP_401_UNAUTHORIZED: {"description": _("api_router.responses.401")},
        status.HTTP_403_FORBIDDEN: {"description": _("api_router.responses.403")},
        status.HTTP_404_NOT_FOUND: {"description": _("api_router.responses.404")},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": _("api_router.responses.422")},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": _("api_router.responses.500")}
    }
)

try:
    api_router.include_router(v1_router, prefix="/v1", tags=[_("api_router.tags.api_v1")]) # "API v1"
    logger.info(_("api_router.log.v1_router_included_successfully"))
except Exception as e:
    logger.warning(_("api_router.log.v1_router_include_failed", error=str(e)))


try:
    api_router.include_router(external_api_router, prefix="/external", tags=[_("api_router.tags.external_api")]) # "Зовнішні API (Вебхуки)"
    logger.info(_("api_router.log.external_router_included_successfully"))
except Exception as e:
    logger.warning(_("api_router.log.external_router_include_failed", error=str(e)))


@api_router.get(
    "/ping",
    summary=_("api_router.ping.summary"), # "Перевірка доступності агрегатора API"
    tags=[_("api_router.tags.api_status")], # "Стан API"
    response_description=_("api_router.ping.response_description") # "Успішна відповідь від ping ендпоінта"
)
async def ping_api():
    """
    Простий ендпоінт для перевірки, чи агрегатор API (`api_router`) працює.
    Повертає статус "Агрегатор API активний!" та повідомлення "Pong!".
    Цей ендпоінт не вимагає автентифікації, якщо глобальні залежності не застосовані.
    """
    logger.debug(_("api_router.log.ping_endpoint_called"))
    return {
        "status": _("api_router.ping.status_message"), # "Агрегатор API активний!"
        "message": _("api_router.ping.pong_message") # "Pong!"
    }


logger.info(_("api_router.log.main_router_configured"))
