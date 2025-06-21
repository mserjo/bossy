# backend/app/src/services/notifications/template.py
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.repositories.notifications.template_repository import NotificationTemplateRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт BaseCacheService
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreate, # Ці імена використовуються в BaseDictionaryService Generic
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
)
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)


# Jinja2 залежність
try:
    from jinja2 import Environment, select_autoescape, StrictUndefined, TemplateSyntaxError, UndefinedError
except ImportError:
    logger.error("Jinja2 не встановлено. Функціонал рендерингу шаблонів не працюватиме.")
    # Можна встановити заглушку або кидати помилку при спробі використання, якщо Jinja2 критично важливий.
    # Для прикладу, залишимо як є, але в реальному проекті це треба обробити.
    StrictUndefined = type('StrictUndefined', (), {})  # Мінімальна заглушка, щоб код не падав при імпорті
    UndefinedError = type('UndefinedError', (Exception,), {})
    TemplateSyntaxError = type('TemplateSyntaxError', (Exception,), {})


    class Environment:  # Заглушка для Environment
        def __init__(self, *args, **kwargs): pass

        def from_string(self, template_string):
            class MockTemplate:
                def render(self, context): return f"Jinja2 не доступний. Необроблений шаблон: {template_string}"

            return MockTemplate()


class NotificationTemplateService(BaseDictionaryService[
                                      NotificationTemplate, # Модель
                                      NotificationTemplateRepository, # Репозиторій
                                      NotificationTemplateCreate, # Схема створення
                                      NotificationTemplateUpdate, # Схема оновлення
                                      NotificationTemplateResponse  # Схема відповіді
                                  ]):
    """
    Сервіс для управління елементами довідника "Шаблони Сповіщень".
    Успадковує CRUD-операції від BaseDictionaryService.
    'code' з BaseDictionary буде використовуватися як унікальний програмний ідентифікатор шаблону.
    'name' - людиночитана назва.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує NotificationTemplateService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        self.template_repo = NotificationTemplateRepository() # Ініціалізація репозиторію
        super().__init__( # Виклик оновленого конструктора BaseDictionaryService
            db_session,
            repository=self.template_repo,
            cache_service=cache_service,
            response_schema=NotificationTemplateResponse
        )
        # _model_name ініціалізується в BaseDictionaryService
        logger.info(f"NotificationTemplateService ініціалізовано для моделі: {self._model_name}")
        # Налаштування середовища Jinja2
        self.jinja_env = Environment(
            autoescape=select_autoescape(['html', 'xml']),  # Базове автоекранування
            undefined=StrictUndefined,  # Кидати помилку для невизначених змінних
            enable_async=True  # Для потенційного асинхронного рендерингу/фільтрів у майбутньому
        )

    async def get_template_by_name(self, name: str) -> Optional[NotificationTemplateResponse]:
        """
        Отримує шаблон сповіщення за його унікальним ім'ям.
        Ім'я використовується як унікальний ідентифікатор для програмного доступу.

        :param name: Унікальне ім'я шаблону.
        :return: Pydantic схема NotificationTemplateResponse або None.
        """
        logger.debug(f"Спроба отримання {self._model_name} за ім'ям: {name}")
        # Використовуємо get_by_code з базового сервісу, передаючи name як code,
        # оскільки 'name' для шаблонів є унікальним ідентифікатором.
        # Це припускає, що модель NotificationTemplate має поле 'name', що відповідає 'code' в логіці BaseDictionaryService.
        # Якщо модель NotificationTemplate має і 'code', і 'name', і вони різні, тоді потрібен окремий метод.
        # Поки що, для узгодження з описом, припускаємо, що 'name' є ключем.
        # У BaseDictionaryService 'code' використовується для get_by_code.
        # Якщо NotificationTemplate не має поля 'code', а унікальність по 'name',
        # то метод get_by_code з базового класу не підійде напряму.
        # Поточна реалізація BaseDictionaryService.create перевіряє унікальність data.code, якщо є.
        # Для NotificationTemplate 'name' є унікальним.
        # TODO: Узгодити використання 'name' vs 'code' з BaseDictionaryService.
        #  Або NotificationTemplate повинен мати поле 'code', або BaseDictionaryService
        #  має бути більш гнучким щодо поля для унікального рядкового ідентифікатора.
        #  Якщо NotificationTemplate.name має бути унікальним ключем для пошуку (як code),
        #  тоді цей метод може бути замінений або доповнений get_by_code з BaseDictionaryService,
        #  якщо 'code' і 'name' - це одне й те саме поле або 'code' використовується як унікальний ключ.
        #  Поточна реалізація репозиторію має get_by_name.
        item_db = await self.template_repo.get_by_name(session=self.db_session, name=name)

        if item_db:
            logger.info(f"{self._model_name} з ім'ям '{name}' знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ім'ям '{name}' не знайдено.")
        return None

    async def list_templates_by_type(
            self,
            template_type: NotificationChannelType, # Змінено str на NotificationChannelType Enum
            skip: int = 0,
            limit: int = 100
    ) -> List[NotificationTemplateResponse]:
        """
        Перелічує всі шаблони сповіщень вказаного типу.
        """
        logger.debug(f"Перелік шаблонів сповіщень типу: '{template_type.value}'")
        # Використовуємо метод репозиторію
        templates_db_list, _ = await self.template_repo.list_by_template_type(
            session=self.db_session,
            template_type=template_type,
            skip=skip,
            limit=limit
        )

        response_list = [self.response_schema.model_validate(t) for t in templates_db_list]
        logger.info(f"Отримано {len(response_list)} шаблонів сповіщень типу '{template_type}'.")
        return response_list

    def render_template(
            self,
            template_content: NotificationTemplateResponse,  # Використовуємо Pydantic модель як джерело шаблонів
            context: Dict[str, Any]
    ) -> Tuple[Optional[str], str]:
        """
        Рендерить тему та тіло шаблону з наданим контекстом, використовуючи Jinja2.
        Це синхронний метод, оскільки рендеринг Jinja2 є CPU-bound операцією.
        Для асинхронних додатків, якщо шаблони дуже великі або контекст об'ємний,
        розгляньте запуск у ThreadPoolExecutor.

        :param template_content: Pydantic схема шаблону (NotificationTemplateResponse).
        :param context: Словник змінних для використання при рендерингу.
        :return: Кортеж (рендерена тема (якщо є), рендерене тіло).
        :raises TemplateSyntaxError: Якщо синтаксична помилка в шаблоні.
        :raises UndefinedError: Якщо в контексті відсутня змінна, що використовується в шаблоні.
        """
        template_name = template_content.name
        logger.debug(f"Рендеринг шаблону '{template_name}' з ключами контексту: {list(context.keys())}")

        rendered_subject: Optional[str] = None
        rendered_body: str

        try:
            if template_content.subject_template:
                jinja_subject_template = self.jinja_env.from_string(template_content.subject_template)
                rendered_subject = jinja_subject_template.render(context)

            jinja_body_template = self.jinja_env.from_string(template_content.body_template)
            rendered_body = jinja_body_template.render(context)

            logger.info(f"Шаблон '{template_name}' успішно відрендерено.")
            return rendered_subject, rendered_body
        except TemplateSyntaxError as e:
            err_msg = _("notification.template.errors.render_syntax_error", template_name=template_name, error_message=e.message, line_number=e.lineno)
            logger.error(f"TemplateSyntaxError for template '{template_name}': {e.message} (line {e.lineno})", exc_info=True)
            raise ValueError(err_msg)
        except UndefinedError as e:  # Jinja2 StrictUndefined кидає UndefinedError
            err_msg = _("notification.template.errors.render_undefined_variable", template_name=template_name, error_message=e.message)
            logger.error(f"UndefinedError for template '{template_name}': {e.message}", exc_info=True)
            raise KeyError(err_msg)
        except Exception as e:  # Інші можливі помилки під час рендерингу
            # Log the original error with more details for developers
            logger.error(f"General rendering error for template '{template_name}': {e}", exc_info=True)
            # For the user, provide a generic fallback message
            fallback_body = _("notification.template.render_fallback.body", template_name=template_name, error_details=str(e))
            fallback_subject = _("notification.template.render_fallback.subject", template_name=template_name) if template_content.subject_template else None
            return fallback_subject, fallback_body

    # CRUD операції (create, update, delete, get_by_id, get_all) успадковуються з BaseDictionaryService.
    # BaseDictionaryService.create та .update будуть перевіряти унікальність поля 'name',
    # якщо модель NotificationTemplate має поле 'name' і воно визначено як унікальне в БД,
    # або якщо логіка перевірки унікальності в BaseDictionaryService налаштована на поле 'name'.
    # Поточна BaseDictionaryService перевіряє 'code' та 'name' якщо вони є в схемі даних.
    # Для NotificationTemplate, 'name' слугує як унікальний ідентифікатор.


logger.debug(f"{NotificationTemplateService.__name__} (сервіс шаблонів сповіщень) успішно визначено.")
