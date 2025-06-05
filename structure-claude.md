# Kudos/Virtus - Детальна структура проекту
# Загальна структура проекту
kudos/
├── README.md                          # Основна документація проекту
├── LICENSE                            # Ліцензія проекту
├── .gitignore                         # Файли та папки для ігнорування Git
├── .env.example                       # Приклад файлу змінних середовища
├── docker-compose.yml                 # Конфігурація Docker для всіх сервісів
├── docker-compose.dev.yml             # Конфігурація Docker для розробки
├── docker-compose.prod.yml            # Конфігурація Docker для продакшну
├── Makefile                           # Автоматизація команд розробки
├── requirements.txt                   # Загальні вимоги для проекту
├── 
├── docs/                             # Документація проекту
│   ├── README.md                     # Індекс документації
│   ├── api/                          # API документація
│   │   ├── openapi.json              # OpenAPI специфікація
│   │   ├── postman/                  # Колекції Postman
│   │   │   ├── kudos_api.postman_collection.json
│   │   │   ├── kudos_environments.postman_environment.json
│   │   │   └── README.md             # Інструкції по використанню Postman
│   │   └── swagger/                  # Swagger UI документація
│   ├── architecture/                 # Архітектурна документація
│   │   ├── system_overview.md        # Загальний огляд системи
│   │   ├── database_design.md        # Дизайн бази даних
│   │   ├── api_design.md             # Дизайн API
│   │   ├── security.md               # Безпека системи
│   │   └── diagrams/                 # Діаграми архітектури
│   │       ├── component_diagram.puml  # Компонентна діаграма (PlantUML)
│   │       ├── database_erd.puml       # ER діаграма бази даних
│   │       ├── business_process.bpmn   # Бізнес-процеси (BPMN)
│   │       └── deployment_diagram.puml # Діаграма розгортання
│   ├── deployment/                   # Документація по розгортанню
│   │   ├── docker.md                 # Інструкції по Docker
│   │   ├── kubernetes.md             # Конфігурація Kubernetes
│   │   └── production.md             # Розгортання в продакшні
│   └── user_guide/                   # Посібник користувача
│       ├── admin_guide.md            # Керівництво адміністратора
│       ├── user_guide.md             # Керівництво користувача
│       └── api_guide.md              # Керівництво по API
│
├── backend/                         # Backend частина проекту
│   ├── Dockerfile                   # Docker файл для backend
│   ├── requirements.txt             # Python залежності
│   ├── requirements-dev.txt         # Залежності для розробки
│   ├── pytest.ini                   # Конфігурація pytest
│   ├── pyproject.toml               # Конфігурація Python проекту
│   ├── alembic.ini                  # Конфігурація Alembic для міграцій
│   ├── .env.example                 # Приклад змінних середовища
│   ├── 
│   ├── app/                         # Основний код додатку
│   │   ├── __init__.py              # Ініціалізація пакету
│   │   ├── main.py                  # Точка входу FastAPI додатку
│   │   ├── 
│   │   └── src/                     # Основний код backend
│   │       ├── __init__.py          # Ініціалізація пакету src
│   │       ├── 
│   │       ├── config/              # Конфігурація додатку
│   │       │   ├── __init__.py      # Ініціалізація пакету config
│   │       │   ├── settings.py      # Налаштування додатку (Pydantic Settings)
│   │       │   ├── database.py      # Конфігурація бази даних
│   │       │   ├── redis.py         # Конфігурація Redis
│   │       │   ├── logging.py       # Конфігурація логування
│   │       │   └── security.py      # Конфігурація безпеки (JWT, паролі)
│   │       │   
│   │       ├── core/                # Основні компоненти системи
│   │       │   ├── __init__.py      # Ініціалізація пакету core
│   │       │   ├── base.py          # Базові класи для всіх моделей
│   │       │   ├── exceptions.py    # Кастомні винятки
│   │       │   ├── constants.py     # Константи системи
│   │       │   ├── dicts.py         # Системні довідники
│   │       │   ├── events.py        # Системні події
│   │       │   ├── permissions.py   # Система дозволів
│   │       │   ├── dependencies.py  # FastAPI dependencies
│   │       │   ├── middleware.py    # Middleware для запитів
│   │       │   ├── validators.py    # Кастомні валідатори
│   │       │   ├── utils.py         # Утилітарні функції
│   │       │   └── i18n.py          # Інтернаціоналізація
│   │       │   
│   │       ├── models/              # SQLAlchemy моделі
│   │       │   ├── __init__.py      # Ініціалізація пакету models
│   │       │   ├── base.py          # Базові класи для моделей
│   │       │   ├── mixins.py        # Міксини для моделей
│   │       │   ├── 
│   │       │   ├── system/           # Системні моделі
│   │       │   │   ├── __init__.py   # Ініціалізація системних моделей
│   │       │   │   ├── settings.py   # Налаштування системи
│   │       │   │   ├── monitoring.py # Моніторинг системи
│   │       │   │   └── health.py     # Health check моделі
│   │       │   │   
│   │       │   ├── dictionaries/      # Довідники
│   │       │   │   ├── __init__.py    # Ініціалізація довідників
│   │       │   │   ├── base_dict.py   # Базовий клас для довідників
│   │       │   │   ├── statuses.py    # Статуси
│   │       │   │   ├── user_roles.py  # Ролі користувачів
│   │       │   │   ├── user_types.py  # Типи користувачів
│   │       │   │   ├── group_types.py # Типи груп
│   │       │   │   ├── task_types.py  # Типи завдань
│   │       │   │   ├── bonus_types.py # Типи бонусів
│   │       │   │   ├── calendars.py   # Календарі
│   │       │   │   └── messengers.py  # Месенджери
│   │       │   │   
│   │       │   ├── auth/            # Аутентифікація
│   │       │   │   ├── __init__.py  # Ініціалізація auth моделей
│   │       │   │   ├── user.py      # Модель користувача
│   │       │   │   ├── token.py     # Токени (JWT, Refresh)
│   │       │   │   └── session.py   # Сесії користувачів
│   │       │   │   
│   │       │   ├── groups/           # Групи
│   │       │   │   ├── __init__.py   # Ініціалізація group моделей
│   │       │   │   ├── group.py      # Основна модель групи
│   │       │   │   ├── settings.py   # Налаштування групи
│   │       │   │   ├── membership.py # Членство в групі
│   │       │   │   └── invitation.py # Запрошення до групи
│   │       │   │   
│   │       │   ├── tasks/            # Завдання та події
│   │       │   │   ├── __init__.py   # Ініціалізація task моделей
│   │       │   │   ├── task.py       # Основна модель завдання
│   │       │   │   ├── event.py      # Модель події
│   │       │   │   ├── assignment.py # Призначення завдань
│   │       │   │   ├── completion.py # Виконання завдань
│   │       │   │   └── review.py     # Відгуки на завдання
│   │       │   │   
│   │       │   ├── bonuses/           # Бонуси та рахунки
│   │       │   │   ├── __init__.py    # Ініціалізація bonus моделей
│   │       │   │   ├── bonus.py       # Модель бонусу
│   │       │   │   ├── account.py     # Рахунок користувача
│   │       │   │   ├── transaction.py # Транзакції
│   │       │   │   └── reward.py      # Нагороди
│   │       │   │   
│   │       │   ├── gamification/      # Геймифікація
│   │       │   │   ├── __init__.py    # Ініціалізація gamification моделей
│   │       │   │   ├── level.py       # Рівні користувачів
│   │       │   │   ├── badge.py       # Бейджі
│   │       │   │   ├── achievement.py # Досягнення
│   │       │   │   └── rating.py      # Рейтинги
│   │       │   │   
│   │       │   ├── notifications/      # Сповіщення
│   │       │   │   ├── __init__.py     # Ініціалізація notification моделей
│   │       │   │   ├── notification.py # Основна модель сповіщення
│   │       │   │   ├── template.py     # Шаблони сповіщень
│   │       │   │   └── delivery.py     # Доставка сповіщень
│   │       │   │   
│   │       │   └── files/           # Файли
│   │       │       ├── __init__.py  # Ініціалізація file моделей
│   │       │       ├── file.py      # Модель файлу
│   │       │       ├── upload.py    # Завантаження файлів
│   │       │       └── avatar.py    # Аватари користувачів
│   │       │       
│   │       ├── schemas/             # Pydantic схеми
│   │       │   ├── __init__.py      # Ініціалізація пакету schemas
│   │       │   ├── base.py          # Базові схеми
│   │       │   ├── 
│   │       │   ├── system/           # Системні схеми
│   │       │   │   ├── __init__.py   # Ініціалізація системних схем
│   │       │   │   ├── settings.py   # Схеми налаштувань системи
│   │       │   │   ├── monitoring.py # Схеми моніторингу
│   │       │   │   └── health.py     # Схеми health check
│   │       │   │   
│   │       │   ├── auth/            # Схеми аутентифікації
│   │       │   │   ├── __init__.py  # Ініціалізація auth схем
│   │       │   │   ├── user.py      # Схеми користувача
│   │       │   │   ├── token.py     # Схеми токенів
│   │       │   │   └── login.py     # Схеми логіну
│   │       │   │   
│   │       │   ├── dictionaries/      # Схеми довідників
│   │       │   │   ├── __init__.py    # Ініціалізація схем довідників
│   │       │   │   ├── base_dict.py   # Базові схеми довідників
│   │       │   │   ├── statuses.py    # Схеми статусів
│   │       │   │   ├── user_roles.py  # Схеми ролей користувачів
│   │       │   │   ├── user_types.py  # Схеми типів користувачів
│   │       │   │   ├── group_types.py # Схеми типів груп
│   │       │   │   ├── task_types.py  # Схеми типів завдань
│   │       │   │   └── bonus_types.py # Схеми типів бонусів
│   │       │   │   
│   │       │   ├── groups/           # Схеми груп
│   │       │   │   ├── __init__.py   # Ініціалізація group схем
│   │       │   │   ├── group.py      # Схеми групи
│   │       │   │   ├── settings.py   # Схеми налаштувань групи
│   │       │   │   ├── membership.py # Схеми членства
│   │       │   │   └── invitation.py # Схеми запрошень
│   │       │   │   
│   │       │   ├── tasks/            # Схеми завдань
│   │       │   │   ├── __init__.py   # Ініціалізація task схем
│   │       │   │   ├── task.py       # Схеми завдання
│   │       │   │   ├── event.py      # Схеми події
│   │       │   │   ├── assignment.py # Схеми призначення
│   │       │   │   ├── completion.py # Схеми виконання
│   │       │   │   └── review.py     # Схеми відгуків
│   │       │   │   
│   │       │   ├── bonuses/           # Схеми бонусів
│   │       │   │   ├── __init__.py    # Ініціалізація bonus схем
│   │       │   │   ├── bonus.py       # Схеми бонусу
│   │       │   │   ├── account.py     # Схеми рахунку
│   │       │   │   ├── transaction.py # Схеми транзакцій
│   │       │   │   └── reward.py      # Схеми нагород
│   │       │   │   
│   │       │   ├── notifications/   # Схеми сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація notification схем
│   │       │   │   ├── notification.py # Схеми сповіщення
│   │       │   │   ├── template.py  # Схеми шаблонів
│   │       │   │   └── delivery.py  # Схеми доставки
│   │       │   │   
│   │       │   └── files/           # Схеми файлів
│   │       │       ├── __init__.py  # Ініціалізація file схем
│   │       │       ├── file.py      # Схеми файлу
│   │       │       ├── upload.py    # Схеми завантаження
│   │       │       └── avatar.py    # Схеми аватарів
│   │       │       
│   │       ├── repositories/        # Репозиторії для роботи з даними
│   │       │   ├── __init__.py      # Ініціалізація пакету repositories
│   │       │   ├── base.py          # Базовий репозиторій
│   │       │   ├── 
│   │       │   ├── system/           # Системні репозиторії
│   │       │   │   ├── __init__.py   # Ініціалізація системних репозиторіїв
│   │       │   │   ├── settings.py   # Репозиторій налаштувань системи
│   │       │   │   ├── monitoring.py # Репозиторій моніторингу
│   │       │   │   └── health.py     # Репозиторій health check
│   │       │   │   
│   │       │   ├── auth/            # Репозиторії аутентифікації
│   │       │   │   ├── __init__.py  # Ініціалізація auth репозиторіїв
│   │       │   │   ├── user.py      # Репозиторій користувача
│   │       │   │   ├── token.py     # Репозиторій токенів
│   │       │   │   └── session.py   # Репозиторій сесій
│   │       │   │   
│   │       │   ├── dictionaries/      # Репозиторії довідників
│   │       │   │   ├── __init__.py    # Ініціалізація репозиторіїв довідників
│   │       │   │   ├── base_dict.py   # Базовий репозиторій довідників
│   │       │   │   ├── statuses.py    # Репозиторій статусів
│   │       │   │   ├── user_roles.py  # Репозиторій ролей користувачів
│   │       │   │   ├── user_types.py  # Репозиторій типів користувачів
│   │       │   │   ├── group_types.py # Репозиторій типів груп
│   │       │   │   ├── task_types.py  # Репозиторій типів завдань
│   │       │   │   └── bonus_types.py # Репозиторій типів бонусів
│   │       │   │   
│   │       │   ├── groups/           # Репозиторії груп
│   │       │   │   ├── __init__.py   # Ініціалізація group репозиторіїв
│   │       │   │   ├── group.py      # Репозиторій групи
│   │       │   │   ├── settings.py   # Репозиторій налаштувань групи
│   │       │   │   ├── membership.py # Репозиторій членства
│   │       │   │   └── invitation.py # Репозиторій запрошень
│   │       │   │   
│   │       │   ├── tasks/            # Репозиторії завдань
│   │       │   │   ├── __init__.py   # Ініціалізація task репозиторіїв
│   │       │   │   ├── task.py       # Репозиторій завдання
│   │       │   │   ├── event.py      # Репозиторій події
│   │       │   │   ├── assignment.py # Репозиторій призначення
│   │       │   │   ├── completion.py # Репозиторій виконання
│   │       │   │   └── review.py     # Репозиторій відгуків
│   │       │   │   
│   │       │   ├── bonuses/           # Репозиторії бонусів
│   │       │   │   ├── __init__.py    # Ініціалізація bonus репозиторіїв
│   │       │   │   ├── bonus.py       # Репозиторій бонусу
│   │       │   │   ├── account.py     # Репозиторій рахунку
│   │       │   │   ├── transaction.py # Репозиторій транзакцій
│   │       │   │   └── reward.py      # Репозиторій нагород
│   │       │   │   
│   │       │   ├── notifications/      # Репозиторії сповіщень
│   │       │   │   ├── __init__.py     # Ініціалізація notification репозиторіїв
│   │       │   │   ├── notification.py # Репозиторій сповіщення
│   │       │   │   ├── template.py     # Репозиторій шаблонів
│   │       │   │   └── delivery.py     # Репозиторій доставки
│   │       │   │   
│   │       │   └── files/           # Репозиторії файлів
│   │       │       ├── __init__.py  # Ініціалізація file репозиторіїв
│   │       │       ├── file.py      # Репозиторій файлу
│   │       │       ├── upload.py    # Репозиторій завантаження
│   │       │       └── avatar.py    # Репозиторій аватарів
│   │       │       
│   │       ├── services/            # Бізнес-логіка
│   │       │   ├── __init__.py      # Ініціалізація пакету services
│   │       │   ├── base.py          # Базовий сервіс
│   │       │   ├── 
│   │       │   ├── system/               # Системні сервіси
│   │       │   │   ├── __init__.py       # Ініціалізація системних сервісів
│   │       │   │   ├── settings.py       # Сервіс налаштувань системи
│   │       │   │   ├── monitoring.py     # Сервіс моніторингу
│   │       │   │   ├── health.py         # Сервіс health check
│   │       │   │   └── initialization.py # Сервіс ініціалізації даних
│   │       │   │   
│   │       │   ├── auth/            # Сервіси аутентифікації
│   │       │   │   ├── __init__.py  # Ініціалізація auth сервісів
│   │       │   │   ├── user.py      # Сервіс користувача
│   │       │   │   ├── token.py     # Сервіс токенів
│   │       │   │   ├── password.py  # Сервіс паролів
│   │       │   │   └── session.py   # Сервіс сесій
│   │       │   │   
│   │       │   ├── dictionaries/      # Сервіси довідників
│   │       │   │   ├── __init__.py    # Ініціалізація сервісів довідників
│   │       │   │   ├── base_dict.py   # Базовий сервіс довідників
│   │       │   │   ├── statuses.py    # Сервіс статусів
│   │       │   │   ├── user_roles.py  # Сервіс ролей користувачів
│   │       │   │   ├── user_types.py  # Сервіс типів користувачів
│   │       │   │   ├── group_types.py # Сервіс типів груп
│   │       │   │   ├── task_types.py  # Сервіс типів завдань
│   │       │   │   └── bonus_types.py # Сервіс типів бонусів
│   │       │   │   
│   │       │   ├── groups/           # Сервіси груп
│   │       │   │   ├── __init__.py   # Ініціалізація group сервісів
│   │       │   │   ├── group.py      # Сервіс групи
│   │       │   │   ├── settings.py   # Сервіс налаштувань групи
│   │       │   │   ├── membership.py # Сервіс членства
│   │       │   │   └── invitation.py # Сервіс запрошень
│   │       │   │   
│   │       │   ├── tasks/            # Сервіси завдань
│   │       │   │   ├── __init__.py   # Ініціалізація task сервісів
│   │       │   │   ├── task.py       # Сервіс завдання
│   │       │   │   ├── event.py      # Сервіс події
│   │       │   │   ├── assignment.py # Сервіс призначення
│   │       │   │   ├── completion.py # Сервіс виконання
│   │       │   │   ├── review.py     # Сервіс відгуків
│   │       │   │   └── scheduler.py  # Сервіс планувальника завдань
│   │       │   │   
│   │       │   ├── bonuses/           # Сервіси бонусів
│   │       │   │   ├── __init__.py    # Ініціалізація bonus сервісів
│   │       │   │   ├── bonus.py       # Сервіс бонусу
│   │       │   │   ├── account.py     # Сервіс рахунку
│   │       │   │   ├── transaction.py # Сервіс транзакцій
│   │       │   │   ├── reward.py      # Сервіс нагород
│   │       │   │   └── calculation.py # Сервіс розрахунків
│   │       │   │   
│   │       │   ├── gamification/      # Сервіси геймифікації
│   │       │   │   ├── __init__.py    # Ініціалізація gamification сервісів
│   │       │   │   ├── level.py       # Сервіс рівней
│   │       │   │   ├── badge.py       # Сервіс бейджів
│   │       │   │   ├── achievement.py # Сервіс досягнень
│   │       │   │   └── rating.py      # Сервіс рейтингів
│   │       │   │   
│   │       │   ├── notifications/   # Сервіси сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація notification сервісів
│   │       │   │   ├── notification.py # Сервіс сповіщення
│   │       │   │   ├── template.py  # Сервіс шаблонів
│   │       │   │   ├── delivery.py  # Сервіс доставки
│   │       │   │   ├── email.py     # Сервіс email
│   │       │   │   ├── sms.py       # Сервіс SMS
│   │       │   │   └── messenger.py # Сервіс месенджерів
│   │       │   │   
│   │       │   ├── integrations/    # Сервіси інтеграцій
│   │       │   │   ├── __init__.py  # Ініціалізація integration сервісів
│   │       │   │   ├── calendar.py  # Сервіс календарів
│   │       │   │   ├── google.py    # Сервіс Google Calendar
│   │       │   │   ├── outlook.py   # Сервіс Outlook
│   │       │   │   ├── telegram.py  # Сервіс Telegram
│   │       │   │   ├── viber.py     # Сервіс Viber
│   │       │   │   ├── slack.py     # Сервіс Slack
│   │       │   │   └── teams.py     # Сервіс Teams
│   │       │   │   
│   │       │   ├── files/           # Сервіси файлів
│   │       │   │   ├── __init__.py  # Ініціалізація file сервісів
│   │       │   │   ├── file.py      # Сервіс файлу
│   │       │   │   ├── upload.py    # Сервіс завантаження
│   │       │   │   ├── avatar.py    # Сервіс аватарів
│   │       │   │   └── storage.py   # Сервіс зберігання
│   │       │   │   
│   │       │   └── cache/           # Сервіси кешування
│   │       │       ├── __init__.py  # Ініціалізація cache сервісів
│   │       │       ├── redis.py     # Сервіс Redis
│   │       │       └── memory.py    # Сервіс memory cache
│   │       │       
│   │       ├── api/                 # API endpoints
│   │       │   ├── __init__.py      # Ініціалізація пакету api
│   │       │   ├── dependencies.py  # Залежності для API
│   │       │   ├── middleware.py    # Middleware для API
│   │       │   ├── router.py        # Головний роутер API
│   │       │   ├── exceptions.py    # Обробники винятків API
│   │       │   ├── 
│   │       │   ├── v1/              # API версії 1
│   │       │   │   ├── __init__.py  # Ініціалізація API v1
│   │       │   │   ├── router.py    # Головний роутер v1
│   │       │   │   ├── 
│   │       │   │   ├── system/           # Системні API endpoints
│   │       │   │   │   ├── __init__.py   # Ініціалізація системних API
│   │       │   │   │   ├── settings.py   # API налаштувань системи
│   │       │   │   │   ├── monitoring.py # API моніторингу
│   │       │   │   │   ├── health.py     # API health check
│   │       │   │   │   └── init_data.py  # API ініціалізації даних
│   │       │   │   │   
│   │       │   │   ├── auth/            # API аутентифікації
│   │       │   │   │   ├── __init__.py  # Ініціалізація auth API
│   │       │   │   │   ├── login.py     # API логіну
│   │       │   │   │   ├── register.py  # API реєстрації
│   │       │   │   │   ├── token.py     # API токенів
│   │       │   │   │   ├── password.py  # API паролів
│   │       │   │   │   └── profile.py   # API профілю
│   │       │   │   │   
│   │       │   │   ├── dictionaries/      # API довідників
│   │       │   │   │   ├── __init__.py    # Ініціалізація API довідників
│   │       │   │   │   ├── statuses.py    # API статусів
│   │       │   │   │   ├── user_roles.py  # API ролей користувачів
│   │       │   │   │   ├── user_types.py  # API типів користувачів
│   │       │   │   │   ├── group_types.py # API типів груп
│   │       │   │   │   ├── task_types.py  # API типів завдань
│   │       │   │   │   ├── bonus_types.py # API типів бонусів
│   │       │   │   │   ├── calendars.py   # API календарів
│   │       │   │   │   └── messengers.py  # API месенджерів
│   │       │   │   │
│   │       │   │   ├── users/           # API управління користувачами (для суперюзера)
│   │       │   │   │   ├── __init__.py  # Ініціалізація user API
│   │       │   │   │   └── users.py     # API для CRUD операцій з користувачами (суперюзер)
│   │       │   │   │   
│   │       │   │   ├── groups/           # API груп
│   │       │   │   │   ├── __init__.py   # Ініціалізація group API
│   │       │   │   │   ├── groups.py     # API груп
│   │       │   │   │   ├── settings.py   # API налаштувань групи
│   │       │   │   │   ├── membership.py # API членства
│   │       │   │   │   ├── invitation.py # API запрошень
│   │       │   │   │   └── reports.py    # API звітів групи
│   │       │   │   │   
│   │       │   │   ├── tasks/            # API завдань
│   │       │   │   │   ├── __init__.py   # Ініціалізація task API
│   │       │   │   │   ├── tasks.py      # API завдань
│   │       │   │   │   ├── events.py     # API подій
│   │       │   │   │   ├── assignments.py # API призначення
│   │       │   │   │   ├── completions.py # API виконання
│   │       │   │   │   └── reviews.py    # API відгуків
│   │       │   │   │   
│   │       │   │   ├── bonuses/          # API бонусів
│   │       │   │   │   ├── __init__.py   # Ініціалізація bonus API
│   │       │   │   │   ├── bonuses.py    # API бонусів
│   │       │   │   │   ├── accounts.py   # API рахунків
│   │       │   │   │   ├── transactions.py # API транзакцій
│   │       │   │   │   └── rewards.py    # API нагород
│   │       │   │   │   
│   │       │   │   ├── gamification/     # API геймифікації
│   │       │   │   │   ├── __init__.py   # Ініціалізація gamification API
│   │       │   │   │   ├── levels.py     # API рівнів
│   │       │   │   │   ├── badges.py     # API бейджів
│   │       │   │   │   ├── achievements.py # API досягнень
│   │       │   │   │   └── ratings.py    # API рейтингів
│   │       │   │   │   
│   │       │   │   ├── notifications/    # API сповіщень
│   │       │   │   │   ├── __init__.py   # Ініціалізація notification API
│   │       │   │   │   ├── notifications.py # API сповіщень
│   │       │   │   │   ├── templates.py  # API шаблонів
│   │       │   │   │   └── delivery.py   # API доставки
│   │       │   │   │   
│   │       │   │   ├── integrations/     # API інтеграцій
│   │       │   │   │   ├── __init__.py   # Ініціалізація integration API
│   │       │   │   │   ├── calendars.py  # API календарів
│   │       │   │   │   └── messengers.py # API месенджерів
│   │       │   │   │   
│   │       │   │   └── files/           # API файлів
│   │       │   │       ├── __init__.py  # Ініціалізація file API
│   │       │   │       ├── files.py     # API файлів
│   │       │   │       ├── uploads.py   # API завантаження
│   │       │   │       └── avatars.py   # API аватарів
│   │       │   │       
│   │       │   └── external/           # API для зовнішніх систем
│   │       │       ├── __init__.py     # Ініціалізація external API
│   │       │       ├── webhook.py      # API вебхуків
│   │       │       ├── calendar.py     # API календарних інтеграцій
│   │       │       └── messenger.py    # API месенджер інтеграцій
│   │       │       
│   │       ├── tasks/               # Фонові завдання
│   │       │   ├── __init__.py      # Ініціалізація пакету tasks
│   │       │   ├── base.py          # Базовий клас для завдань
│   │       │   ├── scheduler.py     # Планувальник завдань
│   │       │   ├── 
│   │       │   ├── system/           # Системні завдання
│   │       │   │   ├── __init__.py   # Ініціалізація системних завдань
│   │       │   │   ├── cleanup.py    # Очищення даних
│   │       │   │   ├── backup.py     # Резервне копіювання
│   │       │   │   └── monitoring.py # Моніторинг системи
│   │       │   │   
│   │       │   ├── notifications/    # Завдання сповіщень
│   │       │   │   ├── __init__.py   # Ініціалізація notification завдань
│   │       │   │   ├── email.py      # Відправка email
│   │       │   │   ├── sms.py        # Відправка SMS
│   │       │   │   └── messenger.py  # Відправка месенджерів
│   │       │   │   
│   │       │   ├── integrations/     # Завдання інтеграцій
│   │       │   │   ├── __init__.py   # Ініціалізація integration завдань
│   │       │   │   ├── calendar.py   # Синхронізація календарів
│   │       │   │   └── messenger.py  # Синхронізація месенджерів
│   │       │   │   
│   │       │   └── gamification/     # Завдання геймифікації
│   │       │       ├── __init__.py   # Ініціалізація gamification завдань
│   │       │       ├── levels.py     # Обчислення рівнів
│   │       │       ├── badges.py     # Видача бейджів
│   │       │       └── ratings.py    # Обчислення рейтингів
│   │       │       
│   │       ├── migrations/          # Міграції бази даних
│   │       │   ├── __init__.py      # Ініціалізація пакету migrations
│   │       │   ├── env.py           # Конфігурація Alembic
│   │       │   ├── script.py.mako   # Шаблон міграції
│   │       │   └── versions/        # Файли міграцій
│   │       │       ├── __init__.py  # Ініціалізація versions
│   │       │       └── README.md    # Документація міграцій
│   │       │       
│   │       ├── utils/               # Утилітарні функції
│   │       │   ├── __init__.py      # Ініціалізація пакету utils
│   │       │   ├── hash.py          # Хешування
│   │       │   ├── security.py      # Безпека
│   │       │   ├── validators.py    # Валідатори
│   │       │   ├── formatters.py    # Форматування
│   │       │   ├── generators.py    # Генератори
│   │       │   ├── converters.py    # Конвертери
│   │       │   └── helpers.py       # Допоміжні функції
│   │       │   
│   │       ├── locales/              # Локалізації
│   │       │   ├── en/               # Англійська
│   │       │   │   └── messages.json # Переклади
│   │       │   └── uk/               # Українська
│   │       │       └── messages.json # Переклади
│   │       │   
│   │       └── static/              # Статичні файли
│   │           ├── images/          # Зображення
│   │           │   ├── avatars/     # Аватари користувачів
│   │           │   ├── groups/      # Іконки груп
│   │           │   ├── rewards/     # Іконки нагород
│   │           │   └── badges/      # Іконки бейджів
│   │           ├── files/           # Файли
│   │           └── temp/            # Тимчасові файли
│   │           
│   ├── tests/                       # Тести backend
│   │   ├── __init__.py              # Ініціалізація пакету tests
│   │   ├── conftest.py              # Конфігурація pytest
│   │   ├── fixtures/                # Фікстури для тестів
│   │   │   ├── __init__.py          # Ініціалізація fixtures
│   │   │   ├── database.py          # Фікстури бази даних
│   │   │   ├── users.py             # Фікстури користувачів
│   │   │   ├── groups.py            # Фікстури груп
│   │   │   ├── tasks.py             # Фікстури завдань
│   │   │   └── bonuses.py           # Фікстури бонусів
│   │   │   
│   │   ├── unit/                    # Юніт тести
│   │   │   ├── __init__.py          # Ініціалізація unit тестів
│   │   │   ├── test_models/         # Тести моделей
│   │   │   │   ├── __init__.py      # Ініціалізація тестів моделей
│   │   │   │   ├── test_auth/       # Тести auth моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів auth моделей
│   │   │   │   │   ├── test_user.py # Тести моделі користувача
│   │   │   │   │   ├── test_token.py # Тести моделі токенів
│   │   │   │   │   └── test_session.py # Тести моделі сесій
│   │   │   │   ├── test_groups/     # Тести group моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів group моделей
│   │   │   │   │   ├── test_group.py # Тести моделі групи
│   │   │   │   │   ├── test_settings.py # Тести налаштувань групи
│   │   │   │   │   ├── test_membership.py # Тести членства
│   │   │   │   │   └── test_invitation.py # Тести запрошень
│   │   │   │   ├── test_tasks/      # Тести task моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів task моделей
│   │   │   │   │   ├── test_task.py # Тести моделі завдання
│   │   │   │   │   ├── test_event.py # Тести моделі події
│   │   │   │   │   ├── test_assignment.py # Тести призначення
│   │   │   │   │   ├── test_completion.py # Тести виконання
│   │   │   │   │   └── test_review.py # Тести відгуків
│   │   │   │   └── test_bonuses/    # Тести bonus моделей
│   │   │   │       ├── __init__.py  # Ініціалізація тестів bonus моделей
│   │   │   │       ├── test_bonus.py # Тести моделі бонусу
│   │   │   │       ├── test_account.py # Тести рахунку
│   │   │   │       ├── test_transaction.py # Тести транзакцій
│   │   │   │       └── test_reward.py # Тести нагород
│   │   │   │       
│   │   │   ├── test_services/       # Тести сервісів
│   │   │   │   ├── __init__.py      # Ініціалізація тестів сервісів
│   │   │   │   ├── test_auth/       # Тести auth сервісів
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів auth сервісів
│   │   │   │   │   ├── test_user.py # Тести сервісу користувача
│   │   │   │   │   ├── test_token.py # Тести сервісу токенів
│   │   │   │   │   └── test_password.py # Тести сервісу паролів
│   │   │   │   ├── test_groups/     # Тести group сервісів
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів group сервісів
│   │   │   │   │   ├── test_group.py # Тести сервісу групи
│   │   │   │   │   ├── test_membership.py # Тести сервісу членства
│   │   │   │   │   └── test_invitation.py # Тести сервісу запрошень
│   │   │   │   ├── test_tasks/      # Тести task сервісів
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів task сервісів
│   │   │   │   │   ├── test_task.py # Тести сервісу завдання
│   │   │   │   │   ├── test_event.py # Тести сервісу події
│   │   │   │   │   └── test_scheduler.py # Тести планувальника
│   │   │   │   └── test_bonuses/    # Тести bonus сервісів
│   │   │   │       ├── __init__.py  # Ініціалізація тестів bonus сервісів
│   │   │   │       ├── test_bonus.py # Тести сервісу бонусу
│   │   │   │       ├── test_account.py # Тести сервісу рахунку
│   │   │   │       └── test_calculation.py # Тести сервісу розрахунків
│   │   │   │       
│   │   │   └── test_utils/          # Тести утиліт
│   │   │       ├── __init__.py      # Ініціалізація тестів утиліт
│   │   │       ├── test_hash.py     # Тести хешування
│   │   │       ├── test_security.py # Тести безпеки
│   │   │       └── test_validators.py # Тести валідаторів
│   │   │       
│   │   ├── integration/             # Інтеграційні тести
│   │   │   ├── __init__.py          # Ініціалізація integration тестів
│   │   │   ├── test_api/            # Тести API
│   │   │   │   ├── __init__.py      # Ініціалізація тестів API
│   │   │   │   ├── test_auth/       # Тести auth API
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів auth API
│   │   │   │   │   ├── test_login.py # Тести API логіну
│   │   │   │   │   ├── test_register.py # Тести API реєстрації
│   │   │   │   │   └── test_token.py # Тести API токенів
│   │   │   │   ├── test_groups/     # Тести group API
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів group API
│   │   │   │   │   ├── test_groups.py # Тести API груп
│   │   │   │   │   ├── test_membership.py # Тести API членства
│   │   │   │   │   └── test_invitation.py # Тести API запрошень
│   │   │   │   ├── test_tasks/      # Тести task API
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів task API
│   │   │   │   │   ├── test_tasks.py # Тести API завдань
│   │   │   │   │   ├── test_events.py # Тести API подій
│   │   │   │   │   └── test_completions.py # Тести API виконання
│   │   │   │   └── test_bonuses/    # Тести bonus API
│   │   │   │       ├── __init__.py  # Ініціалізація тестів bonus API
│   │   │   │       ├── test_bonuses.py # Тести API бонусів
│   │   │   │       ├── test_accounts.py # Тести API рахунків
│   │   │   │       └── test_rewards.py # Тести API нагород
│   │   │   │       
│   │   │   ├── test_database/       # Тести бази даних
│   │   │   │   ├── __init__.py      # Ініціалізація тестів БД
│   │   │   │   ├── test_migrations.py # Тести міграцій
│   │   │   │   ├── test_relationships.py # Тести зв'язків
│   │   │   │   └── test_constraints.py # Тести обмежень
│   │   │   │   
│   │   │   └── test_integrations/   # Тести інтеграцій
│   │   │       ├── __init__.py      # Ініціалізація тестів інтеграцій
│   │   │       ├── test_calendar.py # Тести календарних інтеграцій
│   │   │       ├── test_messenger.py # Тести месенджер інтеграцій
│   │   │       └── test_notifications.py # Тести сповіщень
│   │   │       
│   │   └── e2e/                     # End-to-end тести
│   │       ├── __init__.py          # Ініціалізація e2e тестів
│   │       ├── test_user_flow.py    # Тести потоку користувача
│   │       ├── test_admin_flow.py   # Тести потоку адміністратора
│   │       ├── test_group_flow.py   # Тести потоку групи
│   │       └── test_task_flow.py    # Тести потоку завдань
│   │       
│   ├── scripts/                     # Скрипти
│   │   ├── __init__.py              # Ініціалізація пакету scripts
│   │   ├── start.py                 # Скрипт запуску
│   │   ├── migrate.py               # Скрипт міграцій
│   │   ├── seed.py                  # Скрипт наповнення даних
│   │   ├── backup.py                # Скрипт резервного копіювання
│   │   ├── restore.py               # Скрипт відновлення
│   │   └── cleanup.py               # Скрипт очищення
│   │   
│   └── logs/                        # Логи
│       ├── app.log                  # Логи додатку
│       ├── error.log                # Логи помилок
│       ├── access.log               # Логи доступу
│       └── debug.log                # Логи відладки
│       
├── frontend/                        # Frontend частина проекту
│   ├── README.md                    # Документація frontend
│   ├── pubspec.yaml                 # Конфігурація Flutter проекту
│   ├── pubspec.lock                 # Заблоковані версії залежностей
│   ├── analysis_options.yaml        # Налаштування аналізу коду
│   ├── l10n.yaml                    # Конфігурація локалізації
│   ├── 
│   ├── android/                     # Android специфічні файли
│   │   ├── app/                     # Конфігурація Android додатку
│   │   │   ├── build.gradle         # Gradle скрипт додатку
│   │   │   ├── proguard-rules.pro   # Правила ProGuard
│   │   │   └── src/                 # Вихідний код Android
│   │   │       ├── debug/           # Debug конфігурація
│   │   │       ├── main/            # Основна конфігурація
│   │   │       │   ├── AndroidManifest.xml # Маніфест Android
│   │   │       │   ├── kotlin/      # Kotlin код
│   │   │       │   │   └── com/     # Пакет додатку
│   │   │       │   │       └── example/
│   │   │       │   │           └── kudos/
│   │   │       │   │               └── MainActivity.kt
│   │   │       │   └── res/         # Ресурси Android
│   │   │       │       ├── drawable/      # Зображення
│   │   │       │       ├── mipmap-hdpi/   # Іконки hdpi
│   │   │       │       ├── mipmap-mdpi/   # Іконки mdpi
│   │   │       │       ├── mipmap-xhdpi/  # Іконки xhdpi
│   │   │       │       ├── mipmap-xxhdpi/ # Іконки xxhdpi
│   │   │       │       ├── mipmap-xxxhdpi/ # Іконки xxxhdpi
│   │   │       │       └── values/        # Значення
│   │   │       │           ├── colors.xml # Кольори
│   │   │       │           ├── strings.xml # Рядки
│   │   │       │           └── styles.xml # Стилі
│   │   │       └── profile/         # Profile конфігурація
│   │   ├── build.gradle             # Gradle скрипт проекту
│   │   ├── gradle.properties        # Властивості Gradle
│   │   ├── gradle/                  # Gradle wrapper
│   │   │   └── wrapper/
│   │   │       ├── gradle-wrapper.jar
│   │   │       └── gradle-wrapper.properties
│   │   ├── gradlew                  # Gradle wrapper скрипт (Unix)
│   │   ├── gradlew.bat              # Gradle wrapper скрипт (Windows)
│   │   └── settings.gradle          # Налаштування Gradle
│   │   
│   ├── ios/                         # iOS специфічні файли
│   │   ├── Runner/                  # iOS додаток
│   │   │   ├── Info.plist           # Конфігурація iOS
│   │   │   ├── AppDelegate.swift    # Делегат додатку
│   │   │   ├── Runner-Bridging-Header.h # Bridging header
│   │   │   └── Assets.xcassets/     # Ресурси iOS
│   │   │       └── AppIcon.appiconset/ # Іконки додатку
│   │   ├── Runner.xcodeproj/        # Xcode проект
│   │   │   ├── project.pbxproj      # Файл проекту
│   │   │   └── xcshareddata/        # Спільні дані
│   │   └── Runner.xcworkspace/      # Xcode workspace
│   │       └── contents.xcworkspacedata
│   │       
│   ├── web/                         # Web специфічні файли
│   │   ├── index.html               # HTML файл
│   │   ├── manifest.json            # Web маніфест
│   │   ├── favicon.png              # Іконка сайту
│   │   └── icons/                   # Іконки PWA
│   │       ├── Icon-192.png         # Іконка 192x192
│   │       ├── Icon-512.png         # Іконка 512x512
│   │       └── Icon-maskable-192.png # Maskable іконка
│   │       
│   ├── windows/                     # Windows специфічні файли
│   │   ├── runner/                  # Windows додаток
│   │   │   ├── main.cpp             # Головний файл
│   │   │   ├── resource.h           # Ресурси
│   │   │   ├── runner.exe.manifest  # Маніфест додатку
│   │   │   ├── Runner.rc            # Файл ресурсів
│   │   │   ├── runner.ico           # Іконка додатку
│   │   │   └── win32_window.cpp     # Вікно Win32
