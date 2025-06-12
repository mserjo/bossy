# backend/Dockerfile
# # Dockerfile для збірки образу backend-додатку.
# # Використовує багатостадійну збірку для оптимізації розміру кінцевого образу
# # та для розділення середовищ розробки та продуктиву.

# --- Базовий образ (Base Stage) ---
# Використовуємо офіційний образ Python. Обирайте версію, сумісну з вашим проектом.
FROM python:3.11-slim AS base

# Встановлення змінних середовища
ENV PYTHONDONTWRITEBYTECODE 1  # Запобігає створенню .pyc файлів Python
ENV PYTHONUNBUFFERED 1         # Забезпечує негайний вивід логів Python в консоль

# Встановлення системних залежностей, якщо вони потрібні (наприклад, для psycopg2-binary або інших бібліотек)
# RUN apt-get update && apt-get install -y --no-install-recommends #     # gcc libpq-dev \ # Приклад для psycopg2, якщо не використовується *-binary
#     # netcat-traditional \ # Для очікування запуску БД у entrypoint скрипті
#     && apt-get clean #     && rm -rf /var/lib/apt/lists/*

# Створення робочої директорії
WORKDIR /app

# Створення непривілейованого користувача та групи
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# --- Образ для збірки залежностей (Builder Stage) ---
# Цей етап використовується для встановлення Python залежностей,
# щоб скористатися кешуванням Docker та не встановлювати їх кожного разу при зміні коду.
FROM base AS builder

# Встановлення інструментів для збірки, якщо потрібні для деяких пакетів
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev python3-dev #     && apt-get clean #     && rm -rf /var/lib/apt/lists/*

# Копіювання файлів залежностей
COPY requirements.txt requirements.txt
# Якщо є requirements-dev.txt і деякі з них потрібні для збірки (рідко, але можливо)
# COPY requirements-dev.txt requirements-dev.txt

# Встановлення залежностей
# Використовуйте --no-cache-dir для зменшення розміру шару
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Якщо потрібно, можна створити віртуальне середовище, але для Docker це часто надлишково
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
# RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Образ для розробки (Development Stage) ---
# Цей образ використовується для локальної розробки.
# Він включає вихідний код та залежності для розробки.
FROM base AS development

# Встановлення залежностей для розробки (включаючи основні)
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Копіювання всього коду додатку
# Це буде перезаписано bind mount в docker-compose.dev.yml,
# але корисно для випадків, коли образ використовується без bind mount.
COPY . .

# Встановлення прав для непривілейованого користувача
RUN chown -R appuser:appgroup /app
USER appuser

# Команда за замовчуванням (може бути перевизначена в docker-compose.dev.yml)
# Наприклад, для запуску з --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Образ для продуктиву (Production Stage) ---
# Цей образ оптимізований для продуктивного використання: менший розмір, без зайвих інструментів.
FROM base AS production

# Копіювання встановлених залежностей з етапу 'builder'
# Це дозволяє уникнути повторного встановлення та інструментів збірки в кінцевому образі.
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# Якщо використовували venv на етапі builder:
# COPY --from=builder /opt/venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"


# Копіювання коду додатку
# Важливо копіювати тільки необхідні для запуску файли, щоб зменшити розмір образу.
# Якщо у вас є .dockerignore, він допоможе виключити зайві файли.
COPY . .
# Приклад, якщо ваш додаток знаходиться в папці app:
# COPY ./app /app/app
# COPY ./alembic /app/alembic
# COPY ./scripts /app/scripts # Якщо потрібні для entrypoint
# COPY alembic.ini /app/alembic.ini

# Встановлення прав для непривілейованого користувача
# Переконайтесь, що користувач має права на виконання та запис у потрібні директорії (наприклад, для логів або завантажень)
RUN chown -R appuser:appgroup /app
USER appuser

# Команда для запуску додатку в продуктивному режимі.
# Рекомендується використовувати Gunicorn або інший WSGI/ASGI сервер для продуктиву.
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "-w", "4"]
# Або просто Uvicorn, якщо Gunicorn не використовується:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Можна додати ENTRYPOINT для виконання скриптів перед запуском (наприклад, міграції)
# COPY ./docker-entrypoint.sh /docker-entrypoint.sh
# RUN chmod +x /docker-entrypoint.sh
# ENTRYPOINT ["/docker-entrypoint.sh"] # Цей скрипт потім запустить CMD
