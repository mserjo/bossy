# Makefile for Bossy project

# --- Variables ---
PYTHON_INTERPRETER ?= python3 # Можна перевизначити: make PYTHON_INTERPRETER=python3.11
PIP_INSTALL = $(PYTHON_INTERPRETER) -m pip install
VENV_DIR = .venv # Назва каталогу віртуального середовища
# Припускаємо, що команди docker-compose запускаються з кореня проекту, де знаходиться цей Makefile

# --- Docker Compose Variables ---
# Якщо .env файл знаходиться в корені проекту і містить ці змінні, docker-compose їх підхопить.
# Або їх можна експортувати в середовищі.
# Тут можна задати дефолтні значення, якщо вони не визначені в .env або середовищі.
DB_PORT_HOST ?= 5433
REDIS_PORT_HOST ?= 6380
APP_PORT_HOST ?= 8000

# Файли Docker Compose
COMPOSE_FILES = -f docker-compose.yml
# Для розробки: COMPOSE_FILES_DEV = -f docker-compose.yml -f docker-compose.dev.yml
# Для production: COMPOSE_FILES_PROD = -f docker-compose.yml -f docker-compose.prod.yml

# --- Python Environment ---
# Створення віртуального середовища
venv:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON_INTERPRETER) -m venv $(VENV_DIR)
	@echo "Virtual environment created. Activate with: source $(VENV_DIR)/bin/activate"

# Встановлення залежностей для backend
install-backend:
	@echo "Installing backend dependencies..."
	$(VENV_DIR)/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt
	@echo "Backend dependencies installed."

# Оновлення залежностей для backend
update-backend-deps:
	@echo "Updating backend dependencies..."
	$(VENV_DIR)/bin/pip install --upgrade -r backend/requirements.txt -r backend/requirements-dev.txt
	@echo "Backend dependencies updated."

# --- Linters and Formatters (Backend) ---
# Запускати після активації venv або вказувати шлях до інструментів у venv
lint-backend:
	@echo "Running linters and formatters for backend..."
	$(VENV_DIR)/bin/ruff check backend/app backend/tests
	$(VENV_DIR)/bin/black backend/app backend/tests
	$(VENV_DIR)/bin/mypy backend/app
	@echo "Backend linting and formatting complete."

format-backend:
	@echo "Formatting backend code..."
	$(VENV_DIR)/bin/ruff format backend/app backend/tests
	$(VENV_DIR)/bin/black backend/app backend/tests
	@echo "Backend code formatting complete."

# --- Tests (Backend) ---
test-backend:
	@echo "Running backend tests..."
	cd backend && $(VENV_DIR)/bin/pytest \
		-v \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:reports/coverage \
		tests/
	@echo "Backend tests complete. Coverage report in backend/reports/coverage/index.html"
	@echo "To view coverage: open backend/reports/coverage/index.html"

# --- Database Migrations (Alembic for Backend) ---
# Потребує налаштованого alembic.ini та змінних середовища для БД.
# Запускати з каталогу backend/, де знаходиться alembic.ini
makemigrations-backend:
	@echo "Making backend database migrations..."
	@echo "Enter migration message (e.g., create_users_table):"
	@read msg; \
	cd backend && $(VENV_DIR)/bin/alembic revision -m "$$msg"
	@echo "Backend migration file created."

migrate-backend:
	@echo "Applying backend database migrations..."
	cd backend && $(VENV_DIR)/bin/alembic upgrade head
	@echo "Backend database migrations applied."

# --- Docker Compose Commands ---
# За замовчуванням використовуємо production-like налаштування
# Для запуску dev: make up ARGS="-f docker-compose.dev.yml"
# Або можна створити окрему команду: make up-dev
# `ARGS` дозволяє передавати додаткові файли або опції в docker-compose

# Побудова образів
build:
	@echo "Building Docker images (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) build --parallel --pull
	@echo "Docker images built."

build-dev:
	@echo "Building Docker images for development..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel --pull
	@echo "Development Docker images built."

build-prod:
	@echo "Building Docker images for production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel --pull
	@echo "Production Docker images built."

# Запуск контейнерів у фоновому режимі (-d)
up: build
	@echo "Starting Docker containers in detached mode (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) up -d --remove-orphans
	@echo "Docker containers started."

up-dev: build-dev
	@echo "Starting Docker containers for development in detached mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --remove-orphans
	@echo "Development Docker containers started."

up-prod: build-prod
	@echo "Starting Docker containers for production in detached mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans
	@echo "Production Docker containers started."

# Зупинка контейнерів
down:
	@echo "Stopping Docker containers (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) down
	@echo "Docker containers stopped."

down-dev:
	@echo "Stopping development Docker containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
	@echo "Development Docker containers stopped."

down-prod:
	@echo "Stopping production Docker containers..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "Production Docker containers stopped."

# Перезапуск контейнерів
restart:
	@echo "Restarting Docker containers (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) restart
	@echo "Docker containers restarted."

restart-dev:
	@echo "Restarting development Docker containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart
	@echo "Development Docker containers restarted."

# Перегляд логів (для всіх сервісів або конкретного)
# make logs SERVICE=backend
logs:
	@echo "Showing logs for Docker containers (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) logs -f $(SERVICE)
	# -f для стеження за логами

logs-dev:
	@echo "Showing logs for development Docker containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f $(SERVICE)

# Запуск команди всередині контейнера (наприклад, bash)
# make exec SERVICE=backend CMD="bash"
exec:
	@echo "Executing command '$(CMD)' in service '$(SERVICE)' (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) exec $(SERVICE) $(CMD)

exec-dev:
	@echo "Executing command '$(CMD)' in service '$(SERVICE)' for development..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec $(SERVICE) $(CMD)

# Очищення: зупинка контейнерів та видалення томів (ОБЕРЕЖНО: видаляє дані БД!)
# Використовуйте `make clean` або `make clean-volumes`
clean-containers:
	@echo "Stopping and removing Docker containers (using $(COMPOSE_FILES) $(ARGS))..."
	docker-compose $(COMPOSE_FILES) $(ARGS) down -v --remove-orphans
	@echo "Docker containers and volumes removed."

clean-dev:
	@echo "Stopping and removing development Docker containers and volumes..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v --remove-orphans
	@echo "Development Docker containers and volumes removed."

# Видалення всіх Docker образів, пов'язаних з проектом (ОБЕРЕЖНО!)
# Це може бути корисно, якщо потрібно повністю "чисту" збірку.
# `docker-compose images -q` повертає ID образів.
clean-images:
	@echo "Removing Docker images related to the project (using $(COMPOSE_FILES) $(ARGS))..."
	-docker-compose $(COMPOSE_FILES) $(ARGS) down --rmi all -v # Спробувати видалити образи при зупинці
	# Якщо вище не спрацювало для всіх, можна спробувати так (більш агресивно):
	# -docker images -q -f "label=com.docker.compose.project=$(shell basename $(CURDIR))" | xargs -r docker rmi -f
	@echo "Docker images removed (if any)."

# --- Допоміжні команди ---
help:
	@echo "Bossy Project Makefile"
	@echo "----------------------"
	@echo "Available targets:"
	@echo "  venv                     - Create Python virtual environment for backend"
	@echo "  install-backend          - Install backend Python dependencies into venv"
	@echo "  update-backend-deps      - Update backend Python dependencies in venv"
	@echo ""
	@echo "  lint-backend             - Run linters and formatters for backend code"
	@echo "  format-backend           - Format backend code"
	@echo "  test-backend             - Run backend tests and generate coverage report"
	@echo ""
	@echo "  makemigrations-backend   - Create a new Alembic migration file for backend"
	@echo "  migrate-backend          - Apply Alembic migrations to backend database"
	@echo ""
	@echo "  build                    - Build Docker images (default: prod-like)"
	@echo "  build-dev                - Build Docker images for development"
	@echo "  build-prod               - Build Docker images for production"
	@echo ""
	@echo "  up                       - Start Docker containers (default: prod-like, detached)"
	@echo "  up-dev                   - Start Docker containers for development (detached)"
	@echo "  up-prod                  - Start Docker containers for production (detached)"
	@echo ""
	@echo "  down                     - Stop Docker containers (default: prod-like)"
	@echo "  down-dev                 - Stop development Docker containers"
	@echo "  down-prod                - Stop production Docker containers"
	@echo ""
	@echo "  restart                  - Restart Docker containers (default: prod-like)"
	@echo "  restart-dev              - Restart development Docker containers"
	@echo ""
	@echo "  logs [SERVICE=...]       - View logs from Docker containers (default: prod-like)"
	@echo "  logs-dev [SERVICE=...]   - View logs from development Docker containers"
	@echo ""
	@echo "  exec SERVICE=<name> CMD=<command> - Execute a command in a running container (default: prod-like)"
	@echo "  exec-dev SERVICE=<name> CMD=<command> - Execute a command in a dev container"
	@echo ""
	@echo "  clean-containers         - Stop and remove Docker containers and their volumes (default: prod-like)"
	@echo "  clean-dev                - Stop and remove development containers and volumes"
	@echo "  clean-images             - Remove Docker images related to the project (default: prod-like, CAUTION!)"
	@echo ""
	@echo "  help                     - Show this help message"
	@echo ""
	@echo "Note: For 'build', 'up', 'down', 'restart', 'logs', 'exec', 'clean-images':"
	@echo "  You can pass ARGS to specify compose files, e.g.:"
	@echo "  make up ARGS='-f docker-compose.yml -f docker-compose.dev.yml'"
	@echo "  (This is an alternative to using specific dev/prod targets like 'up-dev')"

.PHONY: venv install-backend update-backend-deps lint-backend format-backend test-backend makemigrations-backend migrate-backend \
	build build-dev build-prod up up-dev up-prod down down-dev down-prod restart restart-dev logs logs-dev exec exec-dev \
	clean-containers clean-dev clean-images help

# TODO: Перевірити шляхи до `requirements.txt` та `alembic` відносно місця запуску make.
#       Поточні команди `cd backend && $(VENV_DIR)/bin/pytest` передбачають, що venv створюється в корені.
#       Якщо venv створюється в `backend/.venv`, то шлях буде `backend/.venv/bin/...`.
#       Поточний `VENV_DIR = .venv` передбачає venv в корені проекту.
# TODO: Узгодити команди `makemigrations-backend` та `migrate-backend` з реальною конфігурацією Alembic.
#       Зокрема, чи потрібен `$(VENV_DIR)/bin/` перед `alembic`, якщо venv активовано.
#       Якщо venv не активовано, то так, шлях потрібен.
# TODO: Додати команди для frontend, якщо/коли він буде.
# TODO: Перевірити команду `clean-images` - вона може бути занадто агресивною або потребувати уточнення міток.
#       `docker-compose down --rmi all` є безпечнішим варіантом для видалення образів, пов'язаних з поточним compose-файлом.
# TODO: Змінні `DB_PORT_HOST`, `REDIS_PORT_HOST`, `APP_PORT_HOST` використовуються для портів.
#       Якщо вони не визначені в `.env` (який docker-compose може підхопити з кореня проекту)
#       або в середовищі, то будуть використані дефолтні значення з `docker-compose.yml`.
#       Тут вони визначені для документації та можливості перевизначення через `make VAR=value ...`.
# TODO: Розглянути можливість додавання команди `init` для початкового налаштування проекту
#       (створення venv, встановлення залежностей, можливо, створення .env з .env.example).
