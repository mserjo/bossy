# backend/app/src/services/tasks/event.py
# -*- coding: utf-8 -*-
from typing import List, Optional, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.event import Event
from backend.app.src.repositories.tasks.event_repository import EventRepository
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.models.tasks.assignment import TaskAssignment

from backend.app.src.schemas.tasks.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailedResponse
)
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

DEFAULT_EVENT_STATUS_CODE = "SCHEDULED"


class EventService(BaseService):
    """
    Сервіс для управління подіями. Події схожі на завдання, але можуть представляти
    заплановані заходи, активності або віхи.
    Цей сервіс надає CRUD-операції та специфічну логіку для подій.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.event_repo = EventRepository() # Ініціалізація репозиторію
        logger.info("EventService ініціалізовано.")

    async def _get_orm_event_with_relations(self, event_id: int, include_details: bool = True) -> Optional[Event]:
        """Внутрішній метод для отримання ORM моделі Event з завантаженням зв'язків."""
        # Залишаємо прямий запит для гнучкого selectinload
        query = select(Event).where(Event.id == event_id)
        if include_details:
            event_type_relation_name = 'event_type' if hasattr(Event, 'event_type') else 'task_type'
            event_type_relation = getattr(Event, event_type_relation_name, None)

            options_to_load = [
                selectinload(Event.group),
                selectinload(Event.status),
                selectinload(Event.created_by_user).options(selectinload(User.user_type)),
                selectinload(Event.updated_by_user).options(selectinload(User.user_type)),
            ]
            if event_type_relation:
                options_to_load.append(selectinload(event_type_relation))
            if hasattr(Event, 'assignments'):
                options_to_load.append(selectinload(Event.assignments).options(
                    selectinload(TaskAssignment.user).options(selectinload(User.user_type))
                ))
            query = query.options(*options_to_load)
        else:
            event_type_relation_name = 'event_type' if hasattr(Event, 'event_type') else 'task_type'
            event_type_relation = getattr(Event, event_type_relation_name, None)
            options = [selectinload(Event.status), selectinload(Event.created_by_user).options(noload("*"))]
            if event_type_relation:
                 options.append(selectinload(event_type_relation))
            query = query.options(*options)

        return (await self.db_session.execute(query)).scalar_one_or_none()

    async def get_event_by_id(self, event_id: int, include_details: bool = False) -> Optional[EventResponse]:
        """
        Отримує подію за її ID.
        Опціонально може включати більше деталей.
        """
        logger.debug(f"Спроба отримання події за ID: {event_id}, include_details: {include_details}")
        event_db = await self._get_orm_event_with_relations(event_id, include_details) # Використовує вже оновлений _get_orm_event_with_relations

        if event_db:
            logger.info(f"Подію з ID '{event_id}' знайдено.")
            response_model = EventDetailedResponse if include_details else EventResponse
            return response_model.model_validate(event_db)

        logger.info(f"Подію з ID '{event_id}' не знайдено.")
        return None

    async def create_event(self, event_create_data: EventCreate, creator_user_id: int) -> EventDetailedResponse:
        """
        Створює нову подію.
        """
        logger.debug(f"Спроба створення нової події '{event_create_data.title}' користувачем ID: {creator_user_id}")

        # Перевірки існування FK залишаються в сервісі
        if not await self.db_session.get(Group, event_create_data.group_id):
            raise ValueError(f"Групу з ID '{event_create_data.group_id}' не знайдено.")

        type_id_to_check = getattr(event_create_data, 'event_type_id', getattr(event_create_data, 'task_type_id', None))
        if not type_id_to_check:
            raise ValueError("Необхідно вказати 'event_type_id' або 'task_type_id' для події.")
        if not await self.db_session.get(TaskType, type_id_to_check): # Припускаємо TaskType для обох
            raise ValueError(f"Тип події/завдання з ID '{type_id_to_check}' не знайдено.")

        status_id_to_set = event_create_data.status_id
        if not status_id_to_set:
            default_status_db = (await self.db_session.execute( # Прямий запит для статусу
                select(Status.id).where(Status.code == DEFAULT_EVENT_STATUS_CODE))
                                 ).scalar_one_or_none()
            if not default_status_db and (not hasattr(Event, 'status_id') or Event.status_id.nullable is False): # type: ignore
                raise ValueError(
                    f"Статус події є обов'язковим, але статус за замовчуванням '{DEFAULT_EVENT_STATUS_CODE}' не знайдено.")
            status_id_to_set = default_status_db
            logger.info(
                f"Для нової події не надано ID статусу, використано статус за замовчуванням ID: {status_id_to_set or 'None (якщо nullable)'}")
        elif not await self.db_session.get(Status, status_id_to_set):
            raise ValueError(f"Статус з ID '{status_id_to_set}' не знайдено.")

        # Підготовка даних для create з репозиторію
        create_dict_for_repo = event_create_data.model_dump(exclude_unset=True)
        create_dict_for_repo['status_id'] = status_id_to_set

        # Узгодження event_type_id/task_type_id
        model_type_id_attr = 'event_type_id' if hasattr(Event, 'event_type_id') else 'task_type_id'
        schema_provided_type_key = 'event_type_id' if 'event_type_id' in create_dict_for_repo else 'task_type_id'
        if schema_provided_type_key in create_dict_for_repo:
            create_dict_for_repo[model_type_id_attr] = create_dict_for_repo.pop(schema_provided_type_key)

        # Створюємо екземпляр схеми, яку очікує репозиторій (EventCreateSchema)
        # Припускаємо, EventCreateSchema = EventCreate
        final_event_create_data = EventCreate(**create_dict_for_repo)

        try:
            new_event_db = await self.event_repo.create(
                session=self.db_session,
                obj_in=final_event_create_data,
                created_by_user_id=creator_user_id,
                updated_by_user_id=creator_user_id
            )
            await self.commit()
            created_event_detailed = await self.get_event_by_id(new_event_db.id, include_details=True)
            if not created_event_detailed:
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати створену подію ID {new_event_db.id} після коміту.")
            logger.info(
                f"Подію '{new_event_db.title}' (ID: {new_event_db.id}) успішно створено користувачем ID '{creator_user_id}'.")
            return created_event_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{event_create_data.title}': {e}", exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося створити подію через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{event_create_data.title}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def update_event(self, event_id: int, event_update_data: EventUpdate, current_user_id: int) -> Optional[EventDetailedResponse]:
        """Оновлює деталі події."""
        logger.debug(f"Спроба оновлення події ID: {event_id} користувачем ID: {current_user_id}")

        event_db = await self.event_repo.get(session=self.db_session, id=event_id) # Використання репозиторію
        if not event_db:
            logger.warning(f"Подію ID '{event_id}' не знайдено для оновлення.")
            return None

        update_data_dict = event_update_data.model_dump(exclude_unset=True)

        # Перевірки FK залишаються в сервісі
        type_id_key_in_update = 'event_type_id' if 'event_type_id' in update_data_dict else 'task_type_id'
        model_type_id_attr = 'event_type_id' if hasattr(Event, 'event_type_id') else 'task_type_id'

        if type_id_key_in_update in update_data_dict and \
                getattr(event_db, model_type_id_attr) != update_data_dict[type_id_key_in_update]:
            if not await self.db_session.get(TaskType, update_data_dict[type_id_key_in_update]):
                raise ValueError(f"Новий тип події/завдання ID '{update_data_dict[type_id_key_in_update]}' не знайдено.")

        if 'status_id' in update_data_dict and event_db.status_id != update_data_dict['status_id']:
            if not await self.db_session.get(Status, update_data_dict['status_id']):
                raise ValueError(f"Новий статус ID '{update_data_dict['status_id']}' не знайдено.")

        # Схема оновлення для репозиторію
        # Потрібно переконатися, що EventUpdateSchema містить всі поля, які можуть бути оновлені,
        # або що BaseRepository.update може приймати dict.
        # Припускаємо, що EventUpdate (який є event_update_data) є правильною схемою.

        # updated_at оновлюється автоматично через TimestampedMixin в BaseRepository.update
        try:
            updated_event_db = await self.event_repo.update(
                session=self.db_session,
                db_obj=event_db,
                obj_in=event_update_data, # Передаємо Pydantic схему EventUpdate
                updated_by_user_id=current_user_id # Передаємо як kwarg
            )
            await self.commit()
            updated_event_detailed = await self.get_event_by_id(updated_event_db.id, include_details=True)
            if not updated_event_detailed:
                raise RuntimeError(f"Критична помилка: не вдалося отримати оновлену подію ID {updated_event_db.id} після коміту.")
            logger.info(f"Подію ID '{event_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_event_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося оновити подію через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка оновлення ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def delete_event(self, event_id: int, current_user_id: int) -> bool: # Змінено UUID на int
        """Видаляє подію."""
        logger.debug(f"Спроба видалення події ID: {event_id} користувачем ID: {current_user_id}")
        event_to_delete = await self.event_repo.get(session=self.db_session, id=event_id) # Використання репозиторію
        if not event_to_delete:
            logger.warning(f"Подію ID '{event_id}' не знайдено для видалення.")
            return False

        event_title_for_log = event_to_delete.title

        try:
            await self.event_repo.remove(session=self.db_session, id=event_id) # Використання репозиторію
            await self.commit()
            logger.info(
                f"Подію ID '{event_id}' (Назва: '{event_title_for_log}') успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при видаленні події ID '{event_id}' ({event_title_for_log}): {e}. Можливо, подія використовується.",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Подія '{event_title_for_log}' використовується і не може бути видалена.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при видаленні події ID '{event_id}' ({event_title_for_log}): {e}", exc_info=global_settings.DEBUG)
            raise

    async def list_events_for_group(
            self, group_id: int, skip: int = 0, limit: int = 100, # Змінено UUID на int
            status_code: Optional[str] = None, event_type_code: Optional[str] = None,
            include_details: bool = False,
            start_date_filter: Optional[datetime] = None,
            end_date_filter: Optional[datetime] = None
    ) -> List[EventResponse]:
        """Перелічує події для групи з фільтрами та пагінацією."""
        logger.debug(
            f"Перелік подій для групи ID: {group_id}, статус: {status_code}, тип: {event_type_code}, деталі: {include_details}, період з {start_date_filter} по {end_date_filter}")

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
            if hasattr(Event, 'assignments'): options.append(selectinload(Event.assignments).options(
                selectinload(TaskAssignment.user).options(selectinload(User.user_type))))
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
            query = query.join(TaskType, getattr(Event, event_type_field_on_model) == TaskType.id).where(
                TaskType.code == event_type_code)

        if start_date_filter and hasattr(Event, 'start_time'):
            query = query.where(Event.start_time >= start_date_filter)
        if end_date_filter:  # Фільтруємо за часом початку події, якщо немає end_time, або за end_time, якщо є
            if hasattr(Event, 'end_time') and Event.end_time is not None:
                query = query.where(Event.end_time <= end_date_filter)
            elif hasattr(Event, 'start_time'):
                query = query.where(Event.start_time <= end_date_filter)

        # Сортування за замовчуванням: за часом початку (новіші спочатку), потім за датою створення
        order_by_attr = getattr(Event, 'start_time', Event.created_at)
        query = query.order_by(order_by_attr.desc().nulls_last(), Event.created_at.desc()).offset(skip).limit(limit)

        events_db = (await self.db_session.execute(query)).scalars().unique().all()

        response_model = EventDetailedResponse if include_details else EventResponse
        response_list = [response_model.model_validate(e) for e in events_db]  # Pydantic v2

        logger.info(f"Отримано {len(response_list)} подій для групи ID '{group_id}'.")
        return response_list


logger.debug(f"{EventService.__name__} (сервіс подій) успішно визначено.")
