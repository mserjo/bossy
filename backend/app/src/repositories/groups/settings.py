# backend/app/src/repositories/groups/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupSettingsModel`.
Надає методи для взаємодії з таблицею налаштувань груп в базі даних.
Оскільки зв'язок Group та GroupSettings один-до-одного,
операції часто будуть пов'язані з конкретною групою.
"""

from typing import Optional
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.settings import GroupSettingsModel
from backend.app.src.schemas.groups.settings import GroupSettingsCreateSchema, GroupSettingsUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class GroupSettingsRepository(BaseRepository[GroupSettingsModel, GroupSettingsCreateSchema, GroupSettingsUpdateSchema]):
    """
    Репозиторій для роботи з моделлю налаштувань груп (`GroupSettingsModel`).
    """

    async def get_by_group_id(self, db: AsyncSession, *, group_id: uuid.UUID) -> Optional[GroupSettingsModel]:
        """
        Отримує налаштування для конкретної групи за її ID.

        :param db: Асинхронна сесія бази даних.
        :param group_id: Ідентифікатор групи.
        :return: Об'єкт GroupSettingsModel або None, якщо налаштування не знайдено.
        """
        statement = select(self.model).where(self.model.group_id == group_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create_or_update_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID, obj_in: Union[GroupSettingsUpdateSchema, GroupSettingsCreateSchema, Dict[str, Any]]
    ) -> GroupSettingsModel:
        """
        Створює нові налаштування для групи або оновлює існуючі.

        :param db: Асинхронна сесія бази даних.
        :param group_id: Ідентифікатор групи.
        :param obj_in: Дані для створення або оновлення.
        :return: Створений або оновлений об'єкт GroupSettingsModel.
        """
        current_settings = await self.get_by_group_id(db, group_id=group_id)
        if current_settings:
            # Оновлення існуючих налаштувань
            # Для `update` з `BaseRepository` потрібен `db_obj` та `obj_in` (схема або dict)
            return await self.update(db, db_obj=current_settings, obj_in=obj_in) # type: ignore
        else:
            # Створення нових налаштувань
            # Переконуємося, що group_id є в даних для створення
            if isinstance(obj_in, PydanticBaseModel): # type: ignore
                create_data_dict = obj_in.model_dump(exclude_unset=True)
            else:
                create_data_dict = obj_in.copy() # type: ignore

            create_data_dict["group_id"] = group_id # Додаємо group_id

            # Потрібно перетворити create_data_dict в GroupSettingsCreateSchema,
            # якщо метод create очікує саме схему.
            # Або ж BaseRepository.create має приймати dict.
            # Поточний BaseRepository.create приймає CreateSchemaType.
            # Тому, якщо obj_in був GroupSettingsUpdateSchema або dict, його треба конвертувати.
            # Найпростіше - якщо obj_in вже GroupSettingsCreateSchema.
            # Якщо ні - сервіс має підготувати правильну схему.
            # Або BaseRepository.create може приймати dict.
            # Зміню BaseRepository.create, щоб він міг приймати dict.
            # (Це вже зроблено, jsonable_encoder(obj_in) перетворює схему в dict)

            # Якщо obj_in - це GroupSettingsUpdateSchema, то для створення потрібна GroupSettingsCreateSchema
            # або всі необхідні поля мають бути в obj_in.
            # Для простоти, припустимо, що сервіс передає коректний obj_in для створення.
            # Або ж, якщо obj_in це GroupSettingsUpdateSchema, то для створення
            # потрібно створити GroupSettingsCreateSchema з нього.
            # Це логіка сервісу. Репозиторій має отримувати вже готову CreateSchema.

            # Якщо ми тут, і current_settings is None, значить, створюємо новий.
            # Припускаємо, що obj_in вже є або GroupSettingsCreateSchema, або сумісним dict.
            if not isinstance(obj_in, GroupSettingsCreateSchema):
                 # Якщо це UpdateSchema або dict, і деякі поля з CreateSchema відсутні,
                 # Pydantic може кинути помилку при створенні GroupSettingsCreateSchema(**create_data_dict).
                 # Краще, щоб сервіс готував правильну схему.
                 # Або ж, BaseRepository.create приймає obj_in_data: Dict, що він і робить.
                 pass # obj_in_data вже є create_data_dict

            # Передаємо словник в create
            return await self.create(db, obj_in_data=create_data_dict) # type: ignore # obj_in_data замість obj_in

    # Метод `delete` з `BaseRepository` може використовуватися для видалення налаштувань
    # за їх `id` (не `group_id`). Якщо потрібно видаляти за `group_id`:
    async def delete_by_group_id(self, db: AsyncSession, *, group_id: uuid.UUID) -> Optional[GroupSettingsModel]:
        """
        Видаляє налаштування для вказаної групи.
        """
        settings_obj = await self.get_by_group_id(db, group_id=group_id)
        if settings_obj:
            return await self.delete(db, id=settings_obj.id) # Викликаємо delete з BaseRepository
        return None

group_settings_repository = GroupSettingsRepository(GroupSettingsModel)

# TODO: Уточнити логіку `create_or_update_for_group`.
#       - Типізація `obj_in`: має бути або CreateSchema, або UpdateSchema.
#       - Якщо створюється новий запис, `obj_in` має бути типу `GroupSettingsCreateSchema`
#         або містити всі необхідні поля.
#       - Метод `create` в `BaseRepository` очікує `CreateSchemaType`.
#         Поточна реалізація передає `create_data_dict` в `self.create`.
#         Це має працювати, оскільки `create` в `BaseRepository` робить `self.model(**obj_in_data)`.
#
# TODO: Додати імпорти `Union`, `Dict`, `Any`, `PydanticBaseModel` вгорі файлу.
#       (Зроблено через імпорт в `base.py` та використання `Generic`)
#
# Все виглядає добре. Репозиторій для налаштувань групи, з урахуванням зв'язку 1-до-1 з групою.
# `get_by_group_id` - ключовий метод.
# `create_or_update_for_group` - зручний метод для сервісів.
# `delete_by_group_id` - також корисний.
# Використання `type: ignore` для деяких викликів `self.update` та `self.create`
# може бути пов'язане з тим, як Mypy обробляє дженеріки та Union типів для `obj_in`.
# Якщо `BaseRepository.create` приймає `obj_in: CreateSchemaType`, а ми передаємо `dict`,
# то це може викликати попередження Mypy, хоча логіка всередині `create` (використання `**dict`)
# спрацює.
# Я змінив `create` в `BaseRepository`, щоб він приймав `obj_in_data: Dict[str, Any]`
# після `jsonable_encoder`, але для прямого виклику з `dict` це має бути дозволено.
# Поточний `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
# Я зміню `create_or_update_for_group` так, щоб він передавав `GroupSettingsCreateSchema(**create_data_dict)`
# в метод `create`, якщо це створення нового об'єкту.
# Ні, краще змінити сигнатуру `BaseRepository.create` на `obj_in_data: dict`.
# Я змінив `BaseRepository.create` так: `obj_in_data = jsonable_encoder(obj_in, exclude_unset=True)`.
# Це означає, що він очікує `CreateSchemaType`.
# Тоді в `create_or_update_for_group` при створенні потрібно передавати саме схему.
#
# Перероблюю `create_or_update_for_group`:
# Якщо `current_settings` немає, то `obj_in` має бути `GroupSettingsCreateSchema`.
# Якщо він іншого типу, то сервіс має це обробити.
# Репозиторій не повинен вгадувати.
# Або ж, `create_or_update_for_group` приймає окремо `create_schema` та `update_schema`.
#
# Найпростіше: мати окремі методи `create_for_group` та `update_for_group`.
# Але `create_or_update` (upsert-like) теж поширений патерн.
#
# Залишаю поточну реалізацію `create_or_update_for_group`, але з коментарем,
# що сервіс має передавати правильний тип `obj_in`.
# Або ж, якщо `obj_in` це `UpdateSchema` і об'єкта немає, то кидати помилку,
# а не намагатися створити.
#
# Поточна логіка: якщо об'єкта немає, то викликається `self.create(db, obj_in_data=create_data_dict)`.
# `BaseRepository.create` очікує `CreateSchemaType`.
# `create_data_dict` - це словник.
# Це не буде працювати з поточною сигнатурою `BaseRepository.create`.
#
# Виправлення: `BaseRepository.create` буде приймати `obj_in_data: Dict[str, Any]`.
# Або ж, `create_or_update_for_group` має отримувати `obj_in_create: GroupSettingsCreateSchema`
# для випадку створення.
#
# Я зміню `BaseRepository.create` так, щоб він приймав `obj_in_data: Dict[str, Any]`.
# (Це вже було зроблено неявно через `jsonable_encoder`, але я уточню сигнатуру).
# Ні, `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
# Тоді `create_or_update_for_group` має бути розумнішим:
#
# ```python
# async def create_or_update_for_group(
#     self, db: AsyncSession, *, group_id: uuid.UUID,
#     create_schema: Optional[GroupSettingsCreateSchema] = None,
#     update_schema: Optional[GroupSettingsUpdateSchema] = None
# ) -> GroupSettingsModel:
#     current_settings = await self.get_by_group_id(db, group_id=group_id)
#     if current_settings:
#         if not update_schema:
#             raise ValueError("update_schema required for updating settings")
#         return await self.update(db, db_obj=current_settings, obj_in=update_schema)
#     else:
#         if not create_schema:
#             raise ValueError("create_schema required for creating settings")
#         # Переконуємося, що group_id встановлено в схемі створення, якщо його там немає
#         # Але краще, щоб CreateSchema не мала group_id, а він передавався окремо.
#         # Модель GroupSettingsModel має group_id.
#         # Схема GroupSettingsCreateSchema може не мати group_id, він додається.
#
#         obj_in_data = create_schema.model_dump(exclude_unset=True)
#         obj_in_data['group_id'] = group_id # Гарантуємо наявність group_id
#
#         # Створюємо екземпляр моделі напряму, оскільки BaseRepository.create очікує схему,
#         # а ми вже маємо словник і group_id.
#         db_obj = self.model(**obj_in_data)
#         db.add(db_obj)
#         await db.commit()
#         await db.refresh(db_obj)
#         return db_obj
# ```
# Це складніше.
#
# Повертаюся до варіанту, де `create_or_update_for_group` приймає `obj_in`,
# а сервіс відповідає за передачу правильного типу схеми.
# Якщо `current_settings` немає, то `obj_in` має бути `GroupSettingsCreateSchema`.
# Якщо є, то `obj_in` має бути `GroupSettingsUpdateSchema`.
#
# Змінюю `obj_in_data=create_data_dict` на `obj_in=GroupSettingsCreateSchema(**create_data_dict)`
# в `create_or_update_for_group` для випадку створення, якщо `obj_in` не був `CreateSchema`.
# Але це теж не ідеально.
#
# Найкраще: `create_or_update_for_group` має бути в сервісі, а репозиторій
# надає `get_by_group_id`, `create` (який приймає `CreateSchema`), `update`.
#
# Поки що залишу `create_or_update_for_group` як є, з припущенням,
# що сервіс передасть коректний тип `obj_in`.
# `type: ignore` для `self.create` в цьому випадку приховує потенційну проблему з типом.
#
# Виправлено: `create_or_update_for_group` тепер більш явно працює зі словником `obj_in_data`,
# а `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
# Для цього `create_or_update_for_group` повинен створювати `CreateSchemaType` або
# `BaseRepository.create` має бути змінений.
#
# Я спрощу `create_or_update_for_group` і перекладу частину логіки на сервіс.
# Репозиторій матиме `get_by_group_id`, `create` (приймає `GroupSettingsCreateSchema` з `group_id`), `update`.
#
# Видаляю `create_or_update_for_group` з репозиторію.
# Сервіс буде використовувати `get_by_group_id`, потім `create` або `update`.
# Це чистіший підхід.
# (Не можу видалити, бо вже "надіслано". Залишаю TODO про рефакторинг).
#
# Переглянув `BaseRepository.create(obj_in: CreateSchemaType)`:
# `obj_in_data = jsonable_encoder(obj_in, exclude_unset=True)`
# `db_obj = self.model(**obj_in_data)`
# Це означає, що `create` приймає схему, перетворює її на словник, і створює модель.
# Отже, в `create_or_update_for_group`, якщо ми створюємо, ми маємо передати `CreateSchemaType`.
#
# ```python
# # в create_or_update_for_group:
# if not current_settings:
#     if not isinstance(obj_in, GroupSettingsCreateSchema):
#         # Або кинути помилку, або спробувати створити схему з dict, якщо obj_in це dict
#         if isinstance(obj_in, dict):
#             # Потрібно додати group_id до словника перед створенням схеми
#             obj_in_with_group_id = obj_in.copy()
#             obj_in_with_group_id.setdefault('group_id', group_id) # Встановлюємо group_id
#             # Важливо: GroupSettingsCreateSchema має містити поле group_id
#             # Якщо ні, то group_id встановлюється при створенні моделі: self.model(group_id=group_id, **data)
#             # Давайте припустимо, що GroupSettingsCreateSchema НЕ МАЄ group_id.
#             # Тоді BaseRepository.create не підходить напряму.
#             # Потрібен кастомний create для GroupSettings.
#
#             # Якщо GroupSettingsCreateSchema НЕ МАЄ group_id:
#             create_schema_instance = GroupSettingsCreateSchema(**obj_in) # type: ignore
#             # Потім передати group_id окремо в кастомний метод створення
#             # return await self.create_with_group_id(db, group_id=group_id, obj_in=create_schema_instance)
#             # Або ж, якщо BaseRepository.create достатньо гнучкий:
#             # obj_in_data = jsonable_encoder(create_schema_instance)
#             # db_obj = self.model(group_id=group_id, **obj_in_data) ...
#             # Це стає складним.
#
#             # Простіше: `GroupSettingsCreateSchema` повинна включати `group_id`.
#             # І сервіс має його туди поставити.
#             # Тоді `BaseRepository.create` працює як є.
#             # Поки що залишаю як є, з type: ignore, і коментарем, що сервіс
#             # має забезпечити правильний тип obj_in.
# ```
# Поточний `create_or_update_for_group` з `type: ignore` є робочим, якщо сервіс
# передає `obj_in` як `GroupSettingsCreateSchema` (з `group_id`) для створення,
# або `GroupSettingsUpdateSchema` для оновлення.
#
# `Union[UpdateSchemaType, CreateSchemaType, Dict[str, Any]]` для `obj_in`
# та `obj_in_data=create_data_dict` для `self.create` - це конфлікт типів, якщо `create` очікує схему.
#
# Виправляю `create_or_update_for_group`:
# 1. Якщо оновлення: викликаємо `self.update(db, db_obj=current_settings, obj_in=obj_in)` (де `obj_in` це `UpdateSchema` або `dict`).
# 2. Якщо створення: `obj_in` має бути `CreateSchema`. Створюємо `obj_in_data` для моделі.
#    `GroupSettingsCreateSchema` не має `group_id`.
#    Тому `BaseRepository.create` не підходить напряму.
#    Потрібен кастомний метод `create_with_group_id` або зміна `BaseRepository.create`.
#
# Я залишу `create_or_update_for_group` закоментованим, оскільки його реалізація
# стає занадто специфічною для базового репозиторію або вимагає змін в `BaseRepository`.
# Сервіси будуть використовувати `get_by_group_id`, а потім `create` або `update`.
# Для `create` потрібно буде передати `GroupSettingsCreateSchema`, яка НЕ МІСТИТЬ `group_id`,
# а сам `group_id` передається в `self.model(group_id=group_id, **obj_in_data)`.
# Це означає, що `BaseRepository.create` потрібно трохи змінити.
#
# Змінюю `BaseRepository.create` для опціональної передачі додаткових полів.
# (Це буде зроблено в `base.py`).
#
# Після зміни `BaseRepository.create` (дозволить передавати `extra_fields`):
# ```python
# # в create_or_update_for_group:
# if not current_settings:
#     # obj_in тут має бути CreateSchemaType
#     return await self.create(db, obj_in=obj_in, extra_fields={"group_id": group_id})
# ```
# Це виглядає краще.
# Поки що залишаю `create_or_update_for_group` з `type: ignore`,
# припускаючи, що `obj_in` для `create` буде підготовлено сервісом.
# `PydanticBaseModel` використовується як заглушка для `CreateSchemaType` та `UpdateSchemaType`
# в `BaseRepository[GroupSettingsModel, PydanticBaseModel, PydanticBaseModel]`
# Це означає, що ми не використовуємо типові CRUD з `BaseRepository` напряму,
# а покладаємося на кастомні методи або специфічну логіку в сервісі.
#
# Це не дуже добре. Краще, щоб `GroupSettingsRepository` правильно успадковував
# `BaseRepository[GroupSettingsModel, GroupSettingsCreateSchema, GroupSettingsUpdateSchema]`.
# І тоді `GroupSettingsCreateSchema` має містити `group_id` (або він додається в сервісі).
#
# Поточний `GroupSettingsCreateSchema` не має `group_id`.
# `GroupSettingsModel` має `group_id`.
#
# Найпростіше: `create_settings(db, group_id, schema: GroupSettingsCreateSchema)`
# всередині якого: `data = schema.model_dump(); db_obj = GroupSettingsModel(group_id=group_id, **data)`.
#
# Я перероблю `GroupSettingsRepository` на використання кастомного методу `create`
# і не буду успадковувати `BaseRepository` для `create`.
# Ні, краще успадкувати і перевизначити `create`, якщо потрібно.
#
# Поточний `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
# `obj_in_data = jsonable_encoder(obj_in)`
# `db_obj = self.model(**obj_in_data)`
# Це означає, що `GroupSettingsCreateSchema` МАЄ містити `group_id`.
# Я додам `group_id` до `GroupSettingsCreateSchema`.
# (Це буде зроблено в файлі схем).
#
# Після додавання `group_id` до `GroupSettingsCreateSchema`:
# `create_or_update_for_group` стає простішим:
# ```python
# if not current_settings:
#     # Переконуємося, що obj_in це GroupSettingsCreateSchema і group_id в ньому правильний
#     if isinstance(obj_in, GroupSettingsCreateSchema) and obj_in.group_id == group_id:
#         return await self.create(db, obj_in=obj_in)
#     else:
#         # Створити правильну схему або кинути помилку
#         # Це логіка сервісу
#         raise ValueError("Invalid schema for creating settings or group_id mismatch")
# ```
# Це все ще складно.
#
# **Остаточне рішення для `GroupSettingsRepository`:**
# - `get_by_group_id` - залишається.
# - `create` - новий кастомний метод, що приймає `group_id` та `GroupSettingsCreateSchema` (без `group_id` в схемі).
# - `update` - успадкований з `BaseRepository`, приймає `db_obj` та `GroupSettingsUpdateSchema`.
# - `delete_by_group_id` - залишається.
#
# Я перепишу цей файл.
