bonus-system/
├── backend/                         # Backend FastAPI додаток
│   ├── app/                         # Основний додаток
│   │   ├── src/                     # Код backend
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # Точка входу FastAPI
│   │   │   ├── config/              # Конфігураційні файли
│   │   │   │   ├── __init__.py
│   │   │   │   ├── settings.py      # Налаштування додатку
│   │   │   │   ├── log_config.py    # Налаштування логування
│   │   │   │   └── database.py      # Конфігурація БД
│   │   │   ├── core/                # Базові компоненти
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py          # JWT аутентифікація
│   │   │   │   ├── security.py      # Безпека та хешування
│   │   │   │   ├── permissions.py   # Система дозволів
│   │   │   │   ├── dependencies.py  # FastAPI dependencies
│   │   │   │   ├── middleware.py    # Middleware для запитів
│   │   │   │   ├── exceptions.py    # Кастомні винятки
│   │   │   │   ├── logging.py       # Конфігурація логування
│   │   │   │   └── i18n.py          # Інтернаціоналізація
│   │   │   ├── models/              # SQLAlchemy моделі
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py          # Базова модель
│   │   │   │   ├── user.py          # Користувачі та ролі
│   │   │   │   ├── group.py         # Групи та типи груп
│   │   │   │   ├── task.py          # Завдання та типи завдань
│   │   │   │   ├── bonus.py         # Бонуси та типи бонусів
│   │   │   │   ├── account.py       # Рахунки користувачів
│   │   │   │   ├── reward.py        # Нагороди
│   │   │   │   ├── transaction.py   # Транзакції (рух бонусів)
│   │   │   │   └── notification.py  # Сповіщення
│   │   │   ├── schemas/             # Pydantic схеми
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py          # Базові схеми
│   │   │   │   ├── auth.py          # Схеми аутентифікації
│   │   │   │   ├── user.py          # Схеми користувачів
│   │   │   │   ├── group.py         # Схеми груп
│   │   │   │   ├── task.py          # Схеми завдань
│   │   │   │   ├── bonus.py         # Схеми бонусів
│   │   │   │   ├── account.py       # Схеми рахунків
│   │   │   │   ├── reward.py        # Схеми нагород
│   │   │   │   ├── notification.py  # Схеми сповіщень
│   │   │   │   └── response.py      # Стандартні відповіді API
│   │   │   ├── api/                 # API endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/              # Версія API v1
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── auth.py      # Аутентифікація
│   │   │   │   │   ├── users.py     # Користувачі
│   │   │   │   │   ├── groups.py    # Групи
│   │   │   │   │   ├── tasks.py     # Завдання
│   │   │   │   │   ├── bonuses.py   # Бонуси
│   │   │   │   │   ├── accounts.py  # Рахунки
│   │   │   │   │   ├── rewards.py   # Нагороди
│   │   │   │   │   ├── notifications.py  # Сповіщення
│   │   │   │   │   ├── ratings.py   # Рейтинги
│   │   │   │   │   ├── files.py     # Файли
│   │   │   │   │   └── admin.py     # Адміністрування
│   │   │   ├── services/            # Бізнес-логіка
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py  # Сервіс аутентифікації
│   │   │   │   ├── user_service.py  # Сервіс користувачів
│   │   │   │   ├── group_service.py # Сервіс груп
│   │   │   │   ├── task_service.py  # Сервіс завдань
│   │   │   │   ├── bonus_service.py # Сервіс бонусів
│   │   │   │   ├── account_service.py      # Сервіс рахунків
│   │   │   │   ├── reward_service.py       # Сервіс нагород
│   │   │   │   ├── notification_service.py # Сервіс сповіщень
│   │   │   │   ├── file_service.py  # Сервіс файлів
│   │   │   │   └── init_service.py  # Ініціалізація системи
│   │   │   ├── repositories/        # Робота з БД
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py               # Базовий репозиторій
│   │   │   │   ├── user_repository.py    # Репозиторій користувачів
│   │   │   │   ├── group_repository.py   # Репозиторій груп
│   │   │   │   ├── task_repository.py    # Репозиторій завдань
│   │   │   │   ├── bonus_repository.py   # Репозиторій бонусів
│   │   │   │   ├── account_repository.py # Репозиторій рахунків
│   │   │   │   └── reward_repository.py  # Репозиторій нагород
│   │   │   ├── locales/             # Переклади
│   │   │   │   ├── en/
│   │   │   │   │   └── messages.json
│   │   │   │   └── uk/
│   │   │   │       └── messages.json
│   │   │   ├── utils/               # Допоміжні утиліти
│   │   │   │   ├── __init__.py
│   │   │   │   ├── helpers.py       # Загальні допоміжні функції
│   │   │   │   ├── validators.py    # Валідатори
│   │   │   │   ├── formatters.py    # Форматувальники
│   │   │   │   ├── constants.py     # Константи
│   │   │   │   └── cache.py         # Робота з Redis
│   │   │   └── tasks/               # Фонові задачі (Celery/asyncio)
│   │   │       ├── __init__.py
│   │   │       ├── celery_app.py    # Конфігурація Celery
│   │   │       ├── notifications.py # Завдання сповіщень
│   │   │       ├── cleanup_tasks.py # Задачі очищення
│   │   │       └── maintenance.py   # Завдання обслуговування
│   ├── alembic/                 # Міграції БД
│   │   ├── versions/            # Файли міграцій
│   │   ├── env.py               # Конфігурація Alembic
│   │   ├── script.py.mako
│   │   └── alembic.ini          # Налаштування Alembic
│   ├── tests/                   # Тести backend
│   │   ├── __init__.py
│   │   ├── conftest.py         # Конфігурація pytest
│   │   ├── unit/                     # Юніт тести
│   │   │   ├── test_models/          # Тести моделей
│   │   │   ├── test_services/        # Тести сервісів
│   │   │   ├── test_repositories/    # Тести репозиторіїв
│   │   ├── integration/              # Інтеграційні тести
│   │   │   ├── test_api/             # Тести API
│   │   │   └── test_auth.py
│   │   ├── fixtures/                 # Тестові дані
│   │   │   └── sample_data.py
│   │   ├── test_config/              # Тести конфігурацій
│   │   ├── test_core/                # Тести ядра
│   │   └── test_utils/               # Тести утиліт
│   ├── scripts/                    # Скрипти
│   │   ├── init_data.py            # Ініціалізація початкових даних
│   │   ├── create_admin.py         # Створення адміністраторів
│   │   ├── backup_db.py            # Резервне копіювання БД
│   │   └── restore_db.py           # Відновлення БД з резервної копії 
│   ├── requirements.txt        # Python залежності
│   ├── requirements-dev.txt    # Залежності для розробки
│   ├── Dockerfile              # Docker образ backend
│   └── .env.example            # Приклад змінних середовища
├── frontend/                       # Flutter додаток
│   ├── lib/                       # Основний код Flutter
│   │   ├── src/                   # Код frontend
│   │   │   ├── main.dart          # Точка входу додатку
│   │   │   ├── app.dart           # Конфігурація додатку
│   │   │   ├── config/            # Конфігурація
│   │   │   │   ├── app_config.dart # Налаштування додатку
│   │   │   │   ├── theme.dart     # Теми оформлення
│   │   │   │   └── routes.dart    # Маршрути навігації
│   │   │   ├── core/              # Базові компоненти
│   │   │   │   ├── constants/     # Константи
│   │   │   │   │   ├── api_constants.dart # API константи
│   │   │   │   │   └── app_constants.dart # Константи додатку
│   │   │   │   ├── errors/        # Обробка помилок
│   │   │   │   │   ├── exceptions.dart    # Винятки
│   │   │   │   │   └── failures.dart      # Помилки
│   │   │   │   ├── network/       # HTTP клієнт
│   │   │   │   │   ├── api_client.dart    # HTTP клієнт
│   │   │   │   │   └── interceptors.dart  # Перехоплювачі запитів
│   │   │   │   ├── utils/         # Утиліти
│   │   │   │   │   ├── validators.dart   # Валідатори
│   │   │   │   │   ├── formatters.dart   # Форматування
│   │   │   │   │   └── logger.dart       # Логування
│   │   │   │   └── storage/       # Локальне збереження
│   │   │   │       ├── secure_storage.dart # Безпечне зберігання
│   │   │   │       └── cache_storage.dart  # Кешування
│   │   │   ├── data/              # Шар даних
│   │   │   │   ├── models/               # Моделі даних
│   │   │   │   │   ├── user_model.dart
│   │   │   │   │   ├── group_model.dart
│   │   │   │   │   ├── task_model.dart
│   │   │   │   │   ├── bonus_model.dart
│   │   │   │   │   ├── account_model.dart
│   │   │   │   │   ├── reward_model.dart
│   │   │   │   │   └── notification_model.dart
│   │   │   │   ├── repositories/         # Репозиторії
│   │   │   │   │   ├── auth_repository.dart
│   │   │   │   │   ├── user_repository.dart
│   │   │   │   │   ├── group_repository.dart
│   │   │   │   │   ├── task_repository.dart
│   │   │   │   │   ├── bonus_repository.dart
│   │   │   │   │   └── notification_repository.dart
│   │   │   │   └── datasources/          # Джерела даних
│   │   │   │       ├── remote/
│   │   │   │       │   ├── auth_remote_datasource.dart
│   │   │   │       │   ├── user_remote_datasource.dart
│   │   │   │       │   └── group_remote_datasource.dart
│   │   │   │       └── local/
│   │   │   │           ├── auth_local_datasource.dart
│   │   │   │           └── cache_datasource.dart
│   │   │   ├── domain/            # Бізнес-логіка
│   │   │   │   ├── entities/             # Сутності домену
│   │   │   │   │   ├── user.dart
│   │   │   │   │   ├── group.dart
│   │   │   │   │   ├── task.dart
│   │   │   │   │   ├── bonus.dart
│   │   │   │   │   ├── account.dart
│   │   │   │   │   ├── reward.dart
│   │   │   │   │   └── notification.dart
│   │   │   │   ├── repositories/         # Абстрактні репозиторії
│   │   │   │   │   ├── auth_repository.dart
│   │   │   │   │   ├── user_repository.dart
│   │   │   │   │   └── group_repository.dart
│   │   │   │   └── usecases/             # Варіанти використання
│   │   │   │       ├── auth/
│   │   │   │       │   ├── login_usecase.dart
│   │   │   │       │   ├── register_usecase.dart
│   │   │   │       │   └── logout_usecase.dart
│   │   │   │       ├── user/
│   │   │   │       │   ├── get_user_profile_usecase.dart
│   │   │   │       │   └── update_profile_usecase.dart
│   │   │   │       └── group/
│   │   │   │           ├── create_group_usecase.dart
│   │   │   │           └── join_group_usecase.dart
│   │   │   ├── presentation/      # UI компоненти
│   │   │   │   ├── dialogs/              # Діалогові вікна
│   │   │   │   ├── bloc/                 # BLoC для управління станом
│   │   │   │   │   ├── auth/
│   │   │   │   │   │   ├── auth_bloc.dart
│   │   │   │   │   │   ├── auth_event.dart
│   │   │   │   │   │   └── auth_state.dart
│   │   │   │   │   ├── user/
│   │   │   │   │   │   ├── user_bloc.dart
│   │   │   │   │   │   ├── user_event.dart
│   │   │   │   │   │   └── user_state.dart
│   │   │   │   │   └── group/
│   │   │   │   │       ├── group_bloc.dart
│   │   │   │   │       ├── group_event.dart
│   │   │   │   │       └── group_state.dart
│   │   │   │   ├── pages/                # Сторінки додатку
│   │   │   │   │   ├── auth/
│   │   │   │   │   │   ├── login_page.dart
│   │   │   │   │   │   ├── register_page.dart
│   │   │   │   │   │   └── forgot_password_page.dart
│   │   │   │   │   ├── home/
│   │   │   │   │   │   ├── home_page.dart
│   │   │   │   │   │   └── dashboard_page.dart
│   │   │   │   │   ├── groups/
│   │   │   │   │   │   ├── groups_list_page.dart
│   │   │   │   │   │   ├── group_details_page.dart
│   │   │   │   │   │   └── create_group_page.dart
│   │   │   │   │   ├── tasks/
│   │   │   │   │   │   ├── tasks_list_page.dart
│   │   │   │   │   │   ├── task_details_page.dart
│   │   │   │   │   │   └── create_task_page.dart
│   │   │   │   │   ├── profile/
│   │   │   │   │   │   ├── profile_page.dart
│   │   │   │   │   │   └── settings_page.dart
│   │   │   │   │   └── notifications/
│   │   │   │   │       └── notifications_page.dart
│   │   │   │   └── widgets/              # Віджети
│   │   │   │       ├── common/
│   │   │   │       │   ├── app_button.dart
│   │   │   │       │   ├── app_text_field.dart
│   │   │   │       │   ├── loading_widget.dart
│   │   │   │       │   └── error_widget.dart
│   │   │   │       ├── auth/
│   │   │   │       │   └── auth_form.dart
│   │   │   │       ├── group/
│   │   │   │       │   ├── group_card.dart
│   │   │   │       │   └── group_members_list.dart
│   │   │   │       └── task/
│   │   │   │           ├── task_card.dart
│   │   │   │           └── task_progress.dart
│   │   │   └── l10n/              # Локалізація
│   │   │       ├── app_localizations.dart
│   │   │       ├── app_localizations_en.dart
│   │   │       └── app_localizations_uk.dart
│   │   ├── assets/                # Ресурси
│   │   │   ├── images/           # Зображення
│   │   │   ├── icons/            # Іконки
│   │   │   └── fonts/            # Шрифти
│   │   ├── test/                 # Тести Flutter
│   │   │   ├── unit/             # Юніт тести
│   │   │   ├── widget/           # Тести віджетів
│   │   │   └── integration/      # Інтеграційні тести
│   │   ├── pubspec.yaml          # Flutter залежності
│   │   ├── Dockerfile           # Docker для Flutter Web
│   │   └── .env.example         # Приклад змінних середовища
│   └── platforms/               # Платформо-специфічні конфігурації
│       ├── android/            # Android конфігурація
│       ├── ios/               # iOS конфігурація
│       ├── web/               # Web конфігурація
│       ├── windows/           # Windows конфігурація
│       └── linux/             # Linux конфігурація
├── docker/                     # Docker конфігурації
│   ├── backend/               # Backend Docker
│   │   ├── Dockerfile         # Production образ
│   │   └── Dockerfile.dev     # Development образ
│   ├── frontend/              # Frontend Docker
│   │   ├── Dockerfile         # Production образ
│   │   └── Dockerfile.dev     # Development образ
│   ├── nginx/                 # Nginx reverse proxy
│   │   ├── nginx.conf         # Конфігурація Nginx
│   │   └── Dockerfile
│   └── postgres/              # PostgreSQL
│       ├── init.sql           # Ініціалізація БД
│       └── Dockerfile
├── docs/                      # Документація
│   ├── api/                   # API документація
│   │   ├── openapi.json       # OpenAPI специфікація
│   │   └── postman/           # Postman колекція
│   ├── architecture/          # Архітектурна документація
│   │   ├── system_design.md   # Системний дизайн
│   │   ├── database_schema.md # Схема БД
│   │   └── diagrams/          # Діаграми
│   │       ├── erd.pdm        # PowerDesigner ER діаграма
│   │       ├── sequence.pdm   # Діаграми послідовності
│   │       └── component.pdm  # Компонентні діаграми
│   ├── deployment/            # Розгортання
│   │   ├── deployment.md      # Інструкції розгортання
│   │   └── configuration.md   # Конфігурація
│   └── user_guide/            # Керівництво користувача
│       ├── admin_guide.md     # Керівництво адміністратора
│       └── user_guide.md      # Керівництво користувача
├── tests/                     # Інтеграційні тести
│   ├── e2e/                   # End-to-end тести
│   ├── api/                   # API тести
│   └── performance/           # Тести продуктивності
├── postman/                   # Postman колекція
│   ├── bonus_system.postman_collection.json
│   └── bonus_system.postman_environment.json
├── .github/                   # GitHub Actions
│   └── workflows/             # CI/CD пайплайни
│       ├── backend_tests.yml  # Тести backend
│       ├── frontend_tests.yml # Тести frontend
│       └── deploy.yml         # Розгортання
├── docker-compose.yml         # Основний compose файл
├── docker-compose.dev.yml     # Compose для розробки
├── docker-compose.prod.yml    # Compose для продакшн
├── .env.example              # Приклад environment змінних
├── .gitignore                # Git ignore файл
├── README.md                 # Опис проекту
└── PROJECT_STRUCTURE.md      # Цей файл


1) Backend:
FastAPI: Швидкий async web framework
SQLAlchemy 2.0: ORM з async підтримкою
Alembic: Міграції БД
Pydantic V2: Валідація та серіалізація
PostgreSQL: Основна БД
Redis: Кешування та черги
JWT: Аутентифікація
Celery: Фонові задачі
Pytest: Тестування

2) Frontend:
Flutter 3.x: Cross-platform framework
BLoC: State management
Dio: HTTP client
Flutter Secure Storage: Безпечне зберігання
Get It: Dependency injection
Auto Route: Навігація
Flutter Test: Тестування

