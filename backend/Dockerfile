# backend/Dockerfile
# Цей Dockerfile призначений для створення Docker-образів backend-додатку.
# Він використовує багатостадійну збірку для оптимізації розміру кінцевого образу,
# покращення кешування шарів та розділення середовищ для розробки та продуктиву.
# Образ базується на Python 3.13.

# --- Етап 1: Базовий образ (Base Stage) ---
# Використовуємо офіційний образ Python 3.13 slim для зменшення розміру.
# "bookworm" є стабільним релізом Debian.
FROM python:3.13-slim-bookworm AS base

# Встановлення глобальних змінних середовища для Python
ENV PYTHONDONTWRITEBYTECODE 1  # Забороняє Python створювати .pyc файли
ENV PYTHONUNBUFFERED 1         # Включає небуферизований вивід stdout/stderr Python, важливо для логування в Docker

# Встановлення системних залежностей, якщо вони потрібні.
# Наприклад, для компіляції деяких Python пакетів або для роботи з базами даних.
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     # build-essential \ # Для компіляції пакетів
#     # libpq-dev \       # Для psycopg2 (якщо не використовується psycopg2-binary)
#     # netcat-traditional \ # Для очікування запуску БД у entrypoint скриптах
#     && apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# Встановлення робочої директорії всередині образу
WORKDIR /app

# Створення непривілейованого користувача та групи для підвищення безпеки.
# Додаток буде запускатися від імені цього користувача.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# --- Етап 2: Образ для збірки залежностей (Builder Stage) ---
# Цей етап призначений для встановлення Python залежностей.
# Результати цього етапу (встановлені пакети) копіюються в наступні етапи,
# що дозволяє ефективно використовувати кешування Docker.
FROM base AS builder

# Встановлення інструментів для збірки, якщо вони потрібні для деяких Python пакетів (наприклад, з C-розширеннями).
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends build-essential libffi-dev python3-dev && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# Оновлення pip та встановлення залежностей
# Використовуємо --no-cache-dir для зменшення розміру шару.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Етап 3: Образ для розробки (Development Stage) ---
# Цей образ призначений для локальної розробки.
# Він включає вихідний код та всі залежності (основні та для розробки).
FROM base AS development

# Встановлення основних залежностей та залежностей для розробки.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt # Встановлюємо основні, потім dev
RUN pip install --no-cache-dir -r requirements-dev.txt

# Копіювання всього коду додатку в робочу директорію /app.
# У docker-compose.dev.yml цей код буде перекритий монтуванням локальної директорії (bind mount),
# але це корисно, якщо образ запускається окремо.
COPY . .

# Надання прав на робочу директорію створеному користувачу.
RUN chown -R appuser:appgroup /app
# Переключення на непривілейованого користувача.
USER appuser

# Команда за замовчуванням для запуску сервера розробки (Uvicorn з --reload).
# Ця команда може бути перевизначена в docker-compose.dev.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Етап 4: Образ для продуктиву (Production Stage) ---
# Цей образ оптимізований для продуктивного середовища: має мінімальний розмір
# та не містить зайвих інструментів для розробки.
FROM base AS production

# Копіювання встановлених Python пакетів з етапу 'builder'.
# Це дозволяє уникнути повторного встановлення залежностей та наявності інструментів збірки
# у кінцевому продуктивному образі. Шлях до site-packages залежить від версії Python.
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
# Копіювання виконуваних файлів, встановлених пакетами (наприклад, alembic, uvicorn, gunicorn).
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Копіювання коду додатку.
# Важливо мати добре налаштований .dockerignore файл, щоб виключити непотрібні файли
# (наприклад, .git, .idea, __pycache__, локальні .env файли тощо) та зменшити розмір образу
# і підвищити безпеку.
COPY . .
# Приклад більш явного копіювання необхідних директорій:
# COPY ./app /app/app
# COPY ./alembic /app/alembic
# COPY ./scripts /app/scripts # Якщо потрібні для entrypoint або CMD
# COPY alembic.ini pyproject.toml README.md /app/ # Копіювання конфігураційних файлів

# Надання прав на робочу директорію створеному користувачу.
RUN chown -R appuser:appgroup /app
# Переключення на непривілейованого користувача.
USER appuser

# Експонування порту, на якому працює додаток.
# Це інформативне налаштування; фактичне прокидання порту відбувається в docker-compose.
EXPOSE 8000

# Команда для запуску додатку в продуктивному режимі.
# Рекомендується використовувати Gunicorn з Uvicorn воркерами для FastAPI.
# Кількість воркерів (`-w`) слід налаштовувати залежно від ресурсів сервера.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "-w", "4"]
# Альтернативно, можна використовувати Uvicorn напряму, якщо Gunicorn не потрібен:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Опціонально: використання entrypoint скрипта для виконання дій перед запуском додатку
# (наприклад, застосування міграцій бази даних).
# COPY ./docker-entrypoint.sh /docker-entrypoint.sh
# RUN chmod +x /docker-entrypoint.sh
# ENTRYPOINT ["/docker-entrypoint.sh"] # Цей скрипт повинен завершуватися командою exec "$@"
                                      # для запуску CMD.
