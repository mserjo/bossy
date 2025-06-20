# backend/app/src/api/external/webhook.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Загальні обробники вебхуків від зовнішніх сервісів.

Цей модуль може містити ендпоінти для прийому вебхуків від сервісів,
для яких ще не створено спеціалізованих обробників (наприклад, у `calendar.py` чи `messenger.py`),
або для дуже загальних потреб інтеграції.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession # Розкоментувати, якщо потрібен доступ до БД

# from backend.app.src.api.dependencies import get_api_db_session # Якщо потрібен доступ до БД
# from backend.app.src.services.external.webhook_service import WebhookService # Приклад майбутнього сервісу
from backend.app.src.config import settings # Для доступу до секретів, якщо потрібна валідація
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.post(
    "/generic",
    summary=_("api_external_webhook.generic.summary"),
    description=_("api_external_webhook.generic.description"),
    deprecated=True,
    response_description=_("api_external_webhook.generic.response_description")
)
async def generic_webhook_receiver(
    request: Request,
    # TODO: Для реального використання додати параметри для валідації, наприклад:
    # x_custom_signature: Optional[str] = Header(None, alias="X-Custom-Signature"),
    # api_key: Optional[str] = Query(None) # Або інший механізм автентифікації
    # db: AsyncSession = Depends(get_api_db_session), # Якщо обробник потребує БД
    # webhook_service: WebhookService = Depends() # Якщо є загальний сервіс
):
    """
    Загальний ендпоінт для прийому вебхуків.
    - Логує заголовки та тіло запиту.
    - **ПОПЕРЕДЖЕННЯ**: Не має вбудованої валідації чи безпеки. Призначений для демонстрації або відладки.
    """
    # TODO: Критично! Перед використанням в реальних умовах, додати надійну валідацію
    #  (перевірка підписів HMAC, IP-адрес, секретних токенів тощо) для кожного очікуваного типу вебхука.
    #  Без валідації цей ендпоінт є вразливим.

    headers = dict(request.headers)
    body = await request.body()

    logger.info(_("api_external_webhook.log.generic_webhook_request_received"))
    logger.info(_("api_external_webhook.log.request_method", method=request.method))
    logger.info(_("api_external_webhook.log.request_url", url=str(request.url)))
    logger.info(_("api_external_webhook.log.client_info",
                 host=request.client.host if request.client else _("api_exceptions.not_applicable_short"),
                 port=request.client.port if request.client else _("api_exceptions.not_applicable_short")))
    logger.info(_("api_external_webhook.log.request_headers", headers=str(headers)))

    try:
        decoded_body = body.decode('utf-8')
        json_body = json.loads(decoded_body)
        logger.info(_("api_external_webhook.log.body_json", body_json=str(json_body)))
    except Exception:
        logger.info(_("api_external_webhook.log.body_raw_not_json", body_raw=body.decode(errors='ignore')[:1000]))

    # Тут може бути логіка для визначення типу вебхука та його маршрутизації
    # ...

    return {
        "status": "received", # Системний статус
        "message": _("api_external_webhook.generic.response_message_received_logged_stub")
    }


logger.info(_("api_external_webhook.log.router_defined_generic"))
