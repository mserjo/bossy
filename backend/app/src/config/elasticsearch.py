# backend/app/src/config/elasticsearch.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування підключення до Elasticsearch,
якщо він використовується в проекті (наприклад, для повнотекстового пошуку
або зберігання та аналізу логів).
"""

from elasticsearch import AsyncElasticsearch # type: ignore # Асинхронна бібліотека для Elasticsearch
from typing import Optional, List, AsyncGenerator

# Імпорт налаштувань Elasticsearch з settings.py
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger

# Глобальна змінна для зберігання клієнта Elasticsearch.
_es_client: Optional[AsyncElasticsearch] = None

async def get_elasticsearch_client() -> Optional[AsyncElasticsearch]:
    """
    Повертає активний асинхронний клієнт Elasticsearch.
    Якщо клієнт ще не створений, намагається його створити.
    """
    global _es_client
    if _es_client is None:
        # TODO: Додати ElasticsearchSettings в settings.py, якщо ще немає.
        # Приклад:
        # class ElasticsearchSettings(BaseSettings):
        #     ELASTICSEARCH_HOSTS: List[Union[HttpUrl, str]] = Field(default=["http://localhost:9200"])
        #     ELASTICSEARCH_USER: Optional[str] = None
        #     ELASTICSEARCH_PASSWORD: Optional[str] = None
        #     # ... інші налаштування Elasticsearch ...
        #     model_config = SettingsConfigDict(env_prefix='ELASTICSEARCH_', ...)
        #
        # settings.elasticsearch: Optional[ElasticsearchSettings]

        es_hosts: Optional[List[str]] = None
        es_user: Optional[str] = None
        es_password: Optional[str] = None

        if hasattr(settings, 'elasticsearch') and settings.elasticsearch:
            es_hosts = [str(host) for host in settings.elasticsearch.ELASTICSEARCH_HOSTS] # Переконуємося, що це список рядків
            # es_user = settings.elasticsearch.ELASTICSEARCH_USER # Якщо є аутентифікація
            # es_password = settings.elasticsearch.ELASTICSEARCH_PASSWORD

        if es_hosts and es_hosts[0]: # Перевіряємо, що список хостів не порожній і перший елемент не порожній рядок
            try:
                logger.info(f"Спроба підключення до Elasticsearch за хостами: {es_hosts}")

                http_auth_params = {}
                # if es_user and es_password: # Застарілий спосіб для http_auth
                #     http_auth_params = (es_user, es_password)
                # Для нових версій elasticsearch-py, basic_auth або api_key краще.
                # Приклад з basic_auth:
                # if es_user and es_password:
                #     _es_client = AsyncElasticsearch(hosts=es_hosts, basic_auth=(es_user, es_password))
                # else:
                #     _es_client = AsyncElasticsearch(hosts=es_hosts)

                # Поки що без αυтентифікації для простоти, якщо вона не налаштована
                _es_client = AsyncElasticsearch(hosts=es_hosts)

                # Перевірка з'єднання
                if not await _es_client.ping():
                    raise ConnectionError("Ping до Elasticsearch не вдався.")
                logger.info("Успішне підключення до Elasticsearch.")

            except ConnectionError as e: # Ловимо ConnectionError від Elasticsearch клієнта
                logger.error(f"Помилка підключення до Elasticsearch (ConnectionError): {e}")
                _es_client = None
            except Exception as e:
                logger.error(f"Невідома помилка при ініціалізації Elasticsearch клієнта: {e}")
                _es_client = None
        else:
            logger.warning("Налаштування Elasticsearch (ELASTICSEARCH_HOSTS) не знайдено або порожні. Elasticsearch не буде використовуватися.")
            return None

    return _es_client

async def close_elasticsearch_client() -> None:
    """
    Закриває клієнт Elasticsearch при завершенні роботи додатку.
    """
    global _es_client
    if _es_client:
        logger.info("Закриття клієнта Elasticsearch.")
        await _es_client.close()
        _es_client = None

# Функція-залежність FastAPI для отримання Elasticsearch клієнта.
async def get_es_client_dependency() -> AsyncGenerator[Optional[AsyncElasticsearch], None]:
    """
    Залежність FastAPI для отримання асинхронного клієнта Elasticsearch.
    Повертає None, якщо Elasticsearch не налаштований або недоступний.
    """
    es_client_instance = await get_elasticsearch_client()
    try:
        yield es_client_instance
    finally:
        # Клієнт Elasticsearch керує своїми з'єднаннями.
        # Явне закриття тут не потрібне для кожного запиту, лише при зупинці додатку.
        pass

# Приклад використання в ендпоінті:
# from fastapi import Depends
# async def search_documents(query: str, es: Optional[AsyncElasticsearch] = Depends(get_es_client_dependency)):
#     if es:
#         response = await es.search(index="my_index", body={"query": {"match": {"content": query}}})
#         return response['hits']['hits']
#     else:
#         # Логіка, якщо Elasticsearch недоступний
#         return {"error": "Elasticsearch service not available"}

# TODO: Додати ElasticsearchSettings в `backend/app/src/config/settings.py`, якщо ще не додано.
# Це включатиме `ELASTICSEARCH_HOSTS` та, можливо, параметри аутентифікації.
#
# TODO: Викликати `get_elasticsearch_client()` (для ініціалізації) та `close_elasticsearch_client()`
# в обробниках подій FastAPI `startup` та `shutdown` в `main.py`, якщо Elasticsearch використовується.
#
# @app.on_event("startup")
# async def startup_event():
#     await get_elasticsearch_client() # Ініціалізує клієнта, якщо налаштовано
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     await close_elasticsearch_client()
#
# Це забезпечить коректне управління ресурсами.
#
# Якщо Elasticsearch не налаштований (немає `ELASTICSEARCH_HOSTS`),
# то `_es_client` залишиться `None`, і залежність повертатиме `None`.
# Це дозволяє додатку працювати без Elasticsearch, якщо він не є критичним
# для всіх функцій (наприклад, використовується лише для опціонального пошуку).
#
# Поточна реалізація передбачає базове підключення без складної аутентифікації.
# Якщо потрібна аутентифікація (basic auth, API key, SSL/TLS),
# параметри `AsyncElasticsearch()` потрібно буде розширити.
#
# Все виглядає як базова заглушка для налаштування Elasticsearch.
# Головне - це наявність `ELASTICSEARCH_HOSTS` в налаштуваннях.
#
# Все готово для базового налаштування Elasticsearch.
