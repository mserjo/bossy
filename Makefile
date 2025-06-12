# Makefile
# Цей Makefile надає набір зручних команд для автоматизації типових завдань
# розробки та управління Docker-контейнерами проекту.
# Він призначений для спрощення взаємодії з проектом та забезпечення консистентності команд.

# --- Змінні ---
# Визначення UID та GID поточного користувача. Це важливо для Linux-систем,
# щоб файли, створені всередині контейнерів, мали правильного власника на хост-машині.
UID := $(shell id -u)
GID := $(shell id -g)

# Базові файли Docker Compose. За замовчуванням використовуються для розробки.
COMPOSE_FILES := -f docker-compose.yml -f docker-compose.dev.yml
DOCKER_COMPOSE := docker-compose $(COMPOSE_FILES)

# Команда для виконання команд всередині 'backend' сервісу.
# Сервіс 'backend' визначений у docker-compose.yml та розширений у docker-compose.dev.yml.
# Права користувача (UID:GID) передаються для коректної роботи з файлами.
BACKEND_SERVICE_NAME := backend # Назва сервісу backend в Docker Compose
BACKEND_EXEC := $(DOCKER_COMPOSE) exec -u $(UID):$(GID) $(BACKEND_SERVICE_NAME)
PYTHON_EXEC := $(BACKEND_EXEC) python # Для запуску Python скриптів всередині контейнера
# Приклад для Alembic, якщо він використовується для міграцій бази даних.
ALEMBIC_EXEC := $(BACKEND_EXEC) alembic

# Кольори для форматування виводу в консоль (опціонально).
GREEN := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
RESET := $(shell tput sgr0)

# Декларація цілей, які не є файлами.
.PHONY: help up down logs build rebuild ps stop clean \
        lint test shell \
        makemigrations migrate \
        superuser seed format \
        prod-up prod-down prod-logs prod-rebuild prod-ps

# --- Основні команди для управління Docker Compose (середовище розробки) ---
help: ## Показати цей список доступних команд та їх опис.
	@echo "${GREEN}Доступні команди:${RESET}"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

up: ## Запустити всі сервіси в режимі розробки (у фоновому режимі).
	@echo "${GREEN}Запуск Docker Compose сервісів для розробки (у фоновому режимі)...${RESET}"
	$(DOCKER_COMPOSE) up -d --remove-orphans
	@echo "${GREEN}Сервіси запущені. Використовуйте 'make logs' для перегляду логів.${RESET}"

down: ## Зупинити та видалити контейнери, мережі (зберігає томи даних).
	@echo "${YELLOW}Зупинка та видалення Docker Compose сервісів (контейнери та мережі)...${RESET}"
	$(DOCKER_COMPOSE) down
	@echo "${GREEN}Сервіси зупинені та видалені.${RESET}"

logs: ## Показати логи всіх сервісів або конкретного (наприклад, make logs service=backend).
	@echo "${GREEN}Перегляд логів сервісів... (Натисніть Ctrl+C для виходу)${RESET}"
	$(DOCKER_COMPOSE) logs -f $(service)

ps: ## Показати статус запущених контейнерів для середовища розробки.
	@echo "${GREEN}Статус контейнерів (середовище розробки):${RESET}"
	$(DOCKER_COMPOSE) ps

stop: ## Зупинити запущені сервіси без їх видалення.
	@echo "${YELLOW}Зупинка сервісів (без видалення)...${RESET}"
	$(DOCKER_COMPOSE) stop
	@echo "${GREEN}Сервіси зупинені.${RESET}"

# --- Команди для збірки та очищення середовища розробки ---
build: ## Зібрати або перезібрати Docker образи (наприклад, make build service=backend).
ifeq ($(no_cache),true)
	@echo "${YELLOW}Перезбірка образу для сервісу $(or $(service), 'всіх сервісів') без кешу...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache $(service)
else
	@echo "${GREEN}Збірка/перезбірка образу для сервісу $(or $(service), 'всіх сервісів')...${RESET}"
	$(DOCKER_COMPOSE) build $(service)
endif

rebuild: ## Перезібрати всі Docker образи для розробки без використання кешу.
	@echo "${YELLOW}Повна перезбірка всіх образів без кешу (середовище розробки)...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "${GREEN}Образи перезібрані.${RESET}"

clean: ## УВАГА! Зупинити, видалити контейнери, мережі, ВСІ томи даних та образи.
	@echo "${YELLOW}УВАГА: Ця команда повністю очистить середовище розробки Docker,${RESET}"
	@echo "${YELLOW}включаючи всі дані в томах (наприклад, дані бази даних!).${RESET}"
	@read -p "Ви абсолютно впевнені, що хочете продовжити? [y/N]: " confirm && \
		[[ $$confirm == [yY] || $$confirm == [уУ] ]] || (echo "Очищення скасовано."; exit 1)
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	@echo "${GREEN}Середовище розробки Docker повністю очищено.${RESET}"

# --- Команди для розробки та тестування (виконуються всередині backend контейнера) ---
lint: ## Запустити лінтери (наприклад, Ruff) для перевірки якості коду.
	@echo "${GREEN}Запуск лінтерів (Ruff) всередині '$(BACKEND_SERVICE_NAME)' контейнера...${RESET}"
	$(BACKEND_EXEC) ruff check .
	# Додайте інші лінтери за потреби:
	# @echo "${GREEN}Запуск MyPy...${RESET}"
	# $(BACKEND_EXEC) mypy .

test: ## Запустити тести (Pytest) всередині backend контейнера.
	@echo "${GREEN}Запуск тестів (Pytest) всередині '$(BACKEND_SERVICE_NAME)' контейнера...${RESET}"
	$(BACKEND_EXEC) pytest tests/
	# Альтернативно, якщо є спеціальний скрипт:
	# $(PYTHON_EXEC) ./scripts/run_tests.py

shell: ## Відкрити інтерактивну оболонку (bash) всередині backend контейнера.
	@echo "${GREEN}Підключення до bash оболонки контейнера '$(BACKEND_SERVICE_NAME)'...${RESET}"
	$(DOCKER_COMPOSE) exec $(BACKEND_SERVICE_NAME) bash

format: ## Форматувати код за допомогою Black та isort всередині backend контейнера.
	@echo "${GREEN}Форматування коду (Black, isort) всередині '$(BACKEND_SERVICE_NAME)' контейнера...${RESET}"
	$(BACKEND_EXEC) black .
	$(BACKEND_EXEC) isort .

# --- Команди для управління базою даних (Alembic, виконуються всередині backend контейнера) ---
makemigrations: ## Створити нову міграцію Alembic (наприклад, make makemigrations message="add_user_model").
	@read -p "${YELLOW}Введіть коротке повідомлення для нової міграції (наприклад, add_user_model): ${RESET}" msg; \
	if [ -z "$$msg" ]; then \
		echo "${YELLOW}Повідомлення не може бути порожнім. Операція скасована.${RESET}"; \
		exit 1; \
	fi; \
	echo "${GREEN}Створення нової Alembic міграції з повідомленням: '$$msg'...${RESET}"; \
	$(ALEMBIC_EXEC) revision -m "$$msg"

migrate: ## Застосувати останні міграції Alembic до бази даних.
	@echo "${GREEN}Застосування Alembic міграцій до бази даних...${RESET}"
	$(ALEMBIC_EXEC) upgrade head

# --- Специфічні команди для додатку (виконуються всередині backend контейнера) ---
superuser: ## Створити суперкористувача (використовує ./scripts/create_superuser.py).
	@echo "${GREEN}Запуск скрипта для створення суперкористувача...${RESET}"
	$(PYTHON_EXEC) ./scripts/create_superuser.py

seed: ## Заповнити базу даних початковими даними (використовує ./scripts/run_seed.py).
	@echo "${GREEN}Запуск скрипта для заповнення бази даних початковими даними...${RESET}"
	$(PYTHON_EXEC) ./scripts/run_seed.py

# --- Команди для продуктивного середовища ---
# Ці команди використовують docker-compose.prod.yml.
PROD_COMPOSE_FILES := -f docker-compose.yml -f docker-compose.prod.yml
PROD_DOCKER_COMPOSE := docker-compose $(PROD_COMPOSE_FILES)

prod-up: ## Запустити сервіси в режимі продуктиву (у фоновому режимі).
	@echo "${GREEN}Запуск Docker Compose сервісів для продуктиву (у фоновому режимі)...${RESET}"
	$(PROD_DOCKER_COMPOSE) up -d --remove-orphans

prod-down: ## Зупинити та видалити контейнери та мережі для продуктиву (зберігає томи).
	@echo "${YELLOW}Зупинка та видалення Docker Compose сервісів (продуктив)...${RESET}"
	$(PROD_DOCKER_COMPOSE) down -v # -v також видаляє іменовані томи, будьте обережні

prod-logs: ## Показати логи всіх сервісів продуктиву або конкретного (наприклад, make prod-logs service=backend).
	@echo "${GREEN}Перегляд логів продуктивних сервісів... (Натисніть Ctrl+C для виходу)${RESET}"
	$(PROD_DOCKER_COMPOSE) logs -f $(service)

prod-rebuild: ## Перезібрати всі Docker образи для продуктиву без використання кешу.
	@echo "${YELLOW}Повна перезбірка всіх образів для продуктиву без кешу...${RESET}"
	$(PROD_DOCKER_COMPOSE) build --no-cache

prod-ps: ## Показати статус запущених контейнерів для продуктивного середовища.
	@echo "${GREEN}Статус контейнерів (продуктивне середовище):${RESET}"
	$(PROD_DOCKER_COMPOSE) ps

# Встановлює 'help' як ціль за замовчуванням, якщо Makefile викликається без аргументів.
.DEFAULT_GOAL := help
