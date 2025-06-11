# backend/app/src/services/tasks/event.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.event import Event # Модель SQLAlchemy Event
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.models.dictionaries.task_types import TaskType # Події можуть використовувати типи завдань або мати свої EventType
from backend.app.src.models.dictionaries.statuses import Status # Для статусу події
from backend.app.src.models.tasks.assignment import TaskAssignment # Якщо події можна "призначати"
# from backend.app.src.models.tasks.rsvp import EventRSVP # Якщо події мають функціонал RSVP

from backend.app.src.schemas.tasks.event import ( # Схеми Pydantic Event
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailedResponse # Розширена схема відповіді
)
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings as global_settings # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Винести коди статусів за замовчуванням (наприклад, "SCHEDULED") в конфігурацію або константи.
DEFAULT_EVENT_STATUS_CODE = "SCHEDULED" # Заплановано

class EventService(BaseService):
    """
    Сервіс для управління подіями. Події схожі на завдання, але можуть представляти
    заплановані заходи, активності або віхи.
    Цей сервіс надає CRUD-операції та специфічну логіку для подій.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("EventService ініціалізовано.")

    async def _get_orm_event_with_relations(self, event_id: UUID, include_details: bool = True) -> Optional[Event]:
        """Внутрішній метод для отримання ORM моделі Event з завантаженням зв'язків."""
        query = select(Event).where(Event.id == event_id)
        if include_details:
            # TODO: Уточнити назву поля для типу події в моделі Event: 'event_type' чи 'task_type'.
            #  Припускаємо, що модель Event може мати поле event_type (зв'язок з TaskType або окремим EventType)
            #  або використовувати task_type, якщо Event є підтипом Task.
            event_type_relation = getattr(Event, 'event_type', getattr(Event, 'task_type', None))

            options_to_load = [
                selectinload(Event.group),
                selectinload(Event.status),
                selectinload(Event.created_by_user).options(selectinload(User.user_type)),
                selectinload(Event.updated_by_user).options(selectinload(User.user_type)),
            ]
            if event_type_relation: # Додаємо, тільки якщо атрибут існує
                 options_to_load.append(selectinload(event_type_relation))
            if hasattr(Event, 'assignments'):
                options_to_load.append(selectinload(Event.assignments).options(
                    selectinload(TaskAssignment.user).options(selectinload(User.user_type))
                ))
            # if hasattr(Event, 'rsvps'): # Якщо є RSVP
            #     options_to_load.append(selectinload(Event.rsvps).options(
            #         selectinload(EventRSVP.user).options(selectinload(User.user_type))
            #     ))
            query = query.options(*options_to_load)
        else: # Для звичайного EventResponse
            query = query.options(
                selectinload(getattr(Event, 'event_type', getattr(Event, 'task_type', None))),
                selectinload(Event.status),
                selectinload(Event.created_by_user).options(noload("*"))
            )
        return (await self.db_session.execute(query)).scalar_one_or_none()

    async def get_event_by_id(self, event_id: UUID, include_details: bool = False) -> Optional[EventResponse]:
        """
        Отримує подію за її ID.
        Опціонально може включати більше деталей.
        """
        logger.debug(f"Спроба отримання події за ID: {event_id}, include_details: {include_details}")
        event_db = await self._get_orm_event_with_relations(event_id, include_details)

        if event_db:
            logger.info(f"Подію з ID '{event_id}' знайдено.")
            response_model = EventDetailedResponse if include_details else EventResponse
            return response_model.model_validate(event_db) # Pydantic v2

        logger.info(f"Подію з ID '{event_id}' не знайдено.")
        return None

    async def create_event(self, event_create_data: EventCreate, creator_user_id: UUID) -> EventDetailedResponse:
        """
        Створює нову подію.

        :param event_create_data: Дані для нової події.
        :param creator_user_id: ID користувача, що створює подію.
        :return: Pydantic схема EventDetailedResponse створеної події.
        :raises ValueError: Якщо пов'язані сутності не знайдено або конфлікт даних. # i18n
        """
        logger.debug(f"Спроба створення нової події '{event_create_data.title}' користувачем ID: {creator_user_id}")

        if not await self.db_session.get(Group, event_create_data.group_id):
            raise ValueError(f"Групу з ID '{event_create_data.group_id}' не знайдено.") # i18n

        # Визначаємо, яке поле для типу використовується: event_type_id чи task_type_id
        type_id_to_check = getattr(event_create_data, 'event_type_id', getattr(event_create_data, 'task_type_id', None))
        if not type_id_to_check:
            # i18n
            raise ValueError("Необхідно вказати 'event_type_id' або 'task_type_id' для події.")

        # Припускаємо, що типи подій зберігаються в TaskType або окремій таблиці EventType
        # TODO: Якщо EventType - окрема модель, замінити TaskType на EventType.
        if not await self.db_session.get(TaskType, type_id_to_check):
            raise ValueError(f"Тип події/завдання з ID '{type_id_to_check}' не знайдено.") # i18n

        status_id_to_set = event_create_data.status_id
        if not status_id_to_set:
            default_status_id = (await self.db_session.execute(
                select(Status.id).where(Status.code == DEFAULT_EVENT_STATUS_CODE)) # Використовуємо DEFAULT_EVENT_STATUS_CODE
            ).scalar_one_or_none()
            if not default_status_id and (not hasattr(Event, 'status_id') or Event.status_id.nullable is False): # type: ignore
                # i18n
                raise ValueError(f"Статус події є обов'язковим, але статус за замовчуванням '{DEFAULT_EVENT_STATUS_CODE}' не знайдено.")
            status_id_to_set = default_status_id
            logger.info(f"Для нової події не надано ID статусу, використано статус за замовчуванням ID: {status_id_to_set or 'None (якщо nullable)'}")
        elif not await self.db_session.get(Status, status_id_to_set):
            raise ValueError(f"Статус з ID '{status_id_to_set}' не знайдено.") # i18n

        event_db_dict = event_create_data.model_dump(exclude_unset=True) # Pydantic v2
        event_db_dict['status_id'] = status_id_to_set

        # Узгодження поля для типу події
        if 'event_type_id' not in event_db_dict and 'task_type_id' in event_db_dict:
            if hasattr(Event, 'event_type_id') and not hasattr(Event, 'task_type_id'):
                event_db_dict['event_type_id'] = event_db_dict.pop('task_type_id')
        elif 'task_type_id' in event_db_dict and not hasattr(Event, 'task_type_id') and hasattr(Event, 'event_type_id'):
             # Якщо схема мала task_type_id, а модель тільки event_type_id, це проблема схеми або мапінгу.
             # Для безпеки, якщо event_type_id є в моделі, використовуємо його.
             if 'event_type_id' not in event_db_dict: # Якщо event_type_id ще не встановлено
                  event_db_dict['event_type_id'] = event_db_dict.pop('task_type_id')
             elif event_db_dict['event_type_id'] != event_db_dict['task_type_id']: # Якщо обидва є, але різні
                  logger.warning("Надано і event_type_id, і task_type_id з різними значеннями. Використано event_type_id.")
                  event_db_dict.pop('task_type_id', None) # Видаляємо task_type_id, якщо є event_type_id
             else: # Обидва є і однакові
                  event_db_dict.pop('task_type_id', None)


        new_event_db = Event(
            **event_db_dict,
            created_by_user_id=creator_user_id,
            updated_by_user_id=creator_user_id # При створенні
        )
        self.db_session.add(new_event_db)
        try:
            await self.commit()
            created_event_detailed = await self.get_event_by_id(new_event_db.id, include_details=True)
            if not created_event_detailed:
                # i18n
                raise RuntimeError(f"Критична помилка: не вдалося отримати створену подію ID {new_event_db.id} після коміту.")
            logger.info(f"Подію '{new_event_db.title}' (ID: {new_event_db.id}) успішно створено користувачем ID '{creator_user_id}'.")
            return created_event_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{event_create_data.title}': {e}", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити подію через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{event_create_data.title}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def update_event(self, event_id: UUID, event_update_data: EventUpdate, current_user_id: UUID) -> Optional[EventDetailedResponse]:
        """Оновлює деталі події."""
        logger.debug(f"Спроба оновлення події ID: {event_id} користувачем ID: {current_user_id}")

        event_db = await self.db_session.get(Event, event_id)
        if not event_db:
            logger.warning(f"Подію ID '{event_id}' не знайдено для оновлення.")
            return None

        update_data = event_update_data.model_dump(exclude_unset=True) # Pydantic v2

        # Узгодження та перевірка типу події
        type_id_key_in_update = 'event_type_id' if 'event_type_id' in update_data else 'task_type_id'
        model_type_id_attr = 'event_type_id' if hasattr(Event, 'event_type_id') else 'task_type_id'

        if type_id_key_in_update in update_data and \
           getattr(event_db, model_type_id_attr) != update_data[type_id_key_in_update]:
            if not await self.db_session.get(TaskType, update_data[type_id_key_in_update]): # Або EventType
                # i18n
                raise ValueError(f"Новий тип події/завдання ID '{update_data[type_id_key_in_update]}' не знайдено.")

        if 'status_id' in update_data and event_db.status_id != update_data['status_id']:
            if not await self.db_session.get(Status, update_data['status_id']):
                # i18n
                raise ValueError(f"Новий статус ID '{update_data['status_id']}' не знайдено.")

        for field, value in update_data.items():
            # Мапінг з схеми на модель, якщо імена полів відрізняються (напр. task_type_id -> event_type_id)
            model_field_name = field
            if field == 'task_type_id' and model_type_id_attr == 'event_type_id':
                model_field_name = 'event_type_id'

            setattr(event_db, model_field_name, value)

        event_db.updated_by_user_id = current_user_id
        event_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(event_db)
        try:
            await self.commit()
            updated_event_detailed = await self.get_event_by_id(event_id, include_details=True)
            if not updated_event_detailed:
                # i18n
                raise RuntimeError(f"Критична помилка: не вдалося отримати оновлену подію ID {event_id} після коміту.")
            logger.info(f"Подію ID '{event_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_event_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити подію через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка оновлення ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def delete_event(self, event_id: UUID, current_user_id: UUID) -> bool:
        """Видаляє подію."""
        # TODO: Політика видалення: каскадне видалення пов'язаних призначень, RSVP? Чи заборона, якщо є залежності?
        logger.debug(f"Спроба видалення події ID: {event_id} користувачем ID: {current_user_id}")
        event_db = await self.db_session.get(Event, event_id)
        if not event_db:
            logger.warning(f"Подію ID '{event_id}' не знайдено для видалення.")
            return False

        try:
            await self.db_session.delete(event_db)
            await self.commit()
            logger.info(f"Подію ID '{event_id}' (Назва: '{event_db.title}') успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{event_id}': {e}. Можливо, подія використовується.", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Подія '{event_db.title}' використовується і не може бути видалена.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{event_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def list_events_for_group(
        self, group_id: UUID, skip: int = 0, limit: int = 100,
        status_code: Optional[str] = None, event_type_code: Optional[str] = None, # `event_type_code` замість `task_type_code`
        include_details: bool = False,
        start_date_filter: Optional[datetime] = None, # Фільтр для подій, що починаються не раніше цієї дати
        end_date_filter: Optional[datetime] = None    # Фільтр для подій, що починаються не пізніше цієї дати
    ) -> List[EventResponse]: # Або List[EventDetailedResponse]
        """Перелічує події для групи з фільтрами та пагінацією."""
        logger.debug(f"Перелік подій для групи ID: {group_id}, статус: {status_code}, тип: {event_type_code}, деталі: {include_details}, період з {start_date_filter} по {end_date_filter}")

        query = select(Event).where(Event.group_id == group_id)

        # Визначення назви поля для типу події в моделі Event
        event_type_attr = getattr(Event, 'event_type', getattr(Event, 'task_type', None))
        event_type_field_on_model = 'event_type_id' if hasattr(Event, 'event_type_id') else 'task_type_id'


        if include_details:
            options = [
                selectinload(Event.status),
                selectinload(Event.created_by_user).options(selectinload(User.user_type)),
                selectinload(Event.updated_by_user).options(selectinload(User.user_type)),
            ]
            if event_type_attr: options.append(selectinload(event_type_attr))
            if hasattr(Event, 'assignments'): options.append(selectinload(Event.assignments).options(selectinload(TaskAssignment.user).options(selectinload(User.user_type))))
            # if hasattr(Event, 'rsvps'): options.append(selectinload(Event.rsvps)) # Якщо є RSVP
            query = query.options(*options)
        else:
            options = [selectinload(Event.status)]
            if event_type_attr: options.append(selectinload(event_type_attr))
            query = query.options(*options)

        if status_code:
            query = query.join(Status, Event.status_id == Status.id).where(Status.code == status_code)
        if event_type_code and hasattr(Event, event_type_field_on_model):
            # TODO: Якщо EventType - окрема модель, замінити TaskType на EventType тут
            query = query.join(TaskType, getattr(Event, event_type_field_on_model) == TaskType.id).where(TaskType.code == event_type_code)

        if start_date_filter and hasattr(Event, 'start_time'):
            query = query.where(Event.start_time >= start_date_filter)
        if end_date_filter: # Фільтруємо за часом початку події, якщо немає end_time, або за end_time, якщо є
            if hasattr(Event, 'end_time') and Event.end_time is not None :
                 query = query.where(Event.end_time <= end_date_filter)
            elif hasattr(Event, 'start_time'):
                 query = query.where(Event.start_time <= end_date_filter)

        # Сортування за замовчуванням: за часом початку (новіші спочатку), потім за датою створення
        order_by_attr = getattr(Event, 'start_time', Event.created_at)
        query = query.order_by(order_by_attr.desc().nulls_last(), Event.created_at.desc()).offset(skip).limit(limit)

        events_db = (await self.db_session.execute(query)).scalars().unique().all()

        response_model = EventDetailedResponse if include_details else EventResponse
        response_list = [response_model.model_validate(e) for e in events_db] # Pydantic v2

        logger.info(f"Отримано {len(response_list)} подій для групи ID '{group_id}'.")
        return response_list

logger.debug(f"{EventService.__name__} (сервіс подій) успішно визначено.")
