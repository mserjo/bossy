# backend/app/src/schemas/system/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `SystemSettingModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні системних налаштувань.
"""

from pydantic import Field, field_validator, model_validator, BaseModel as PydanticBaseModel
from typing import Optional, Any, Dict, Union
import uuid
from datetime import datetime
import json # Для валідації JSON значень

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema

# --- Схема для відображення системного налаштування (для читання) ---
class SystemSettingSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення системного налаштування.
    """
    key: str = Field(..., description="Унікальний ключ налаштування")
    value: Optional[Any] = Field(None, description="Значення налаштування (тип залежить від value_type)")
    value_type: str = Field(..., description="Тип значення ('string', 'integer', 'boolean', 'json', 'float', 'list_string')")
    description: Optional[str] = Field(None, description="Опис призначення цього налаштування")
    is_editable: bool = Field(..., description="Чи може це налаштування редагуватися через UI")
    # category: Optional[str] = Field(None, description="Категорія налаштування для групування в UI") # Якщо буде в моделі

    # Валідатор для перетворення збереженого рядкового значення `value` у відповідний тип
    # на основі `value_type` при читанні з БД (from_attributes=True).
    # Або ж це перетворення має відбуватися на сервісному рівні перед передачею в схему.
    # Pydantic v2: @model_validator(mode='before') - якщо дані з ORM, то це вже буде правильного типу.
    # Якщо value в моделі завжди str, то тут потрібен @model_validator(mode='after')
    # або краще, щоб сервіс готував дані.
    # Поки що припускаємо, що сервіс передає вже розпарсений `value`.
    # Але для надійності, якщо `value` з моделі завжди `str`:
    @model_validator(mode='before')
    @classmethod
    def convert_value_from_string(cls, data: Any) -> Any:
        if isinstance(data, PydanticBaseModel): # Якщо це вже модель (наприклад, з ORM)
            _value = data.value
            _value_type = data.value_type
        elif isinstance(data, dict): # Якщо це словник
            _value = data.get('value')
            _value_type = data.get('value_type')
        else:
            return data # Не можемо обробити, повертаємо як є

        if _value is None:
            return data

        try:
            if _value_type == 'integer':
                data.value = int(_value)
            elif _value_type == 'float':
                data.value = float(_value)
            elif _value_type == 'boolean':
                # Дозволяємо різні представлення boolean
                if isinstance(_value, str):
                    val_lower = _value.lower()
                    if val_lower in ['true', '1', 'yes', 'on']:
                        data.value = True
                    elif val_lower in ['false', '0', 'no', 'off']:
                        data.value = False
                    else:
                        # Залишаємо як є, якщо не розпізнано, або можна кинути помилку
                        pass # Або raise ValueError(f"Invalid boolean string: {_value}")
                # Якщо вже bool, то нічого не робимо
            elif _value_type == 'json':
                if isinstance(_value, str): # Якщо з БД прийшов рядок JSON
                    data.value = json.loads(_value)
            elif _value_type == 'list_string':
                if isinstance(_value, str): # Очікуємо рядок типу "item1,item2,item3"
                    data.value = [item.strip() for item in _value.split(',') if item.strip()]
            # 'string' залишається як є
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            # Якщо конвертація не вдалася, можна повернути помилку валідації
            # або залишити значення як є (рядок) і покластися на подальшу обробку.
            # Поки що не змінюємо, якщо помилка, щоб не переривати процес.
            # TODO: Вирішити, як обробляти помилки конвертації. Можливо, краще кидати ValueError.
            pass
        return data


# --- Схема для створення нового системного налаштування ---
class SystemSettingCreateSchema(BaseSchema):
    """
    Схема для створення нового системного налаштування.
    """
    key: str = Field(..., min_length=1, max_length=255, description="Унікальний ключ налаштування")
    value: Optional[Any] = Field(None, description="Значення налаштування") # Тип буде валідуватися далі
    value_type: str = Field(..., description="Тип значення ('string', 'integer', 'boolean', 'json', 'float', 'list_string')")
    description: Optional[str] = Field(None, description="Опис призначення цього налаштування")
    is_editable: bool = Field(default=True, description="Чи може це налаштування редагуватися через UI")
    # category: Optional[str] = Field(None, description="Категорія налаштування")

    @field_validator('key')
    @classmethod
    def key_format(cls, value: str) -> str:
        """Валідатор для поля key: дозволяє літери, цифри, крапки та підкреслення."""
        if not all(c.isalnum() or c in ['.', '_'] for c in value):
            raise ValueError('Ключ повинен містити лише літери, цифри, крапки (.) та символ підкреслення (_).')
        return value.lower()

    @field_validator('value_type')
    @classmethod
    def allowed_value_types(cls, value: str) -> str:
        allowed_types = ['string', 'integer', 'boolean', 'json', 'float', 'list_string']
        if value not in allowed_types:
            raise ValueError(f"Недопустимий тип значення. Дозволені типи: {', '.join(allowed_types)}")
        return value

    # Валідатор для перевірки відповідності `value` до `value_type`
    # та для серіалізації `value` в рядок для збереження в моделі, якщо модель зберігає все як Text.
    # Якщо модель SystemSettingModel.value є Text.
    @model_validator(mode='after') # Після валідації окремих полів
    def validate_value_against_type_and_serialize(cls, data: 'SystemSettingCreateSchema') -> 'SystemSettingCreateSchema':
        _value = data.value
        _value_type = data.value_type

        if _value is None: # Дозволяємо NULL значення
            return data

        try:
            if _value_type == 'integer':
                if not isinstance(_value, int): raise ValueError("Значення має бути цілим числом")
                data.value = str(_value) # Серіалізація в рядок для моделі
            elif _value_type == 'float':
                if not isinstance(_value, (int, float)): raise ValueError("Значення має бути числом (float)")
                data.value = str(_value) # Серіалізація в рядок
            elif _value_type == 'boolean':
                if not isinstance(_value, bool): raise ValueError("Значення має бути булевим (true/false)")
                data.value = str(_value).lower() # Серіалізація в "true" або "false"
            elif _value_type == 'json':
                # Перевірка, чи значення є валідним JSON (може бути dict або list)
                # Pydantic автоматично розпарсить JSON рядок в dict/list, якщо він прийшов як рядок.
                # Якщо прийшов dict/list, то він вже валідний для JSON.
                # Тут ми серіалізуємо його назад в рядок JSON для збереження в моделі.
                json.dumps(_value) # Перевірка на можливість серіалізації
                data.value = json.dumps(_value) # Серіалізація в рядок JSON
            elif _value_type == 'list_string':
                if not (isinstance(_value, list) and all(isinstance(item, str) for item in _value)):
                    raise ValueError("Значення має бути списком рядків")
                data.value = ",".join(_value) # Серіалізація в рядок через кому
            elif _value_type == 'string':
                if not isinstance(_value, str): raise ValueError("Значення має бути рядком")
                # data.value залишається як є (вже рядок)
            else:
                # Це не повинно статися, якщо `allowed_value_types` валідатор спрацював
                raise ValueError(f"Невідомий value_type: {_value_type}")
        except ValueError as e: # Ловимо ValueError з наших перевірок
            raise ValueError(f"Помилка валідації значення для типу '{_value_type}': {e}")
        except TypeError as e: # Ловимо TypeError, наприклад, від json.dumps
            raise ValueError(f"Помилка типу значення для типу '{_value_type}': {e}")
        except Exception as e: # Інші можливі помилки
             raise ValueError(f"Неочікувана помилка при валідації значення для типу '{_value_type}': {e}")
        return data


# --- Схема для оновлення існуючого системного налаштування ---
class SystemSettingUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого системного налаштування.
    Оновлювати можна лише `value`. `key`, `value_type`, `description`, `is_editable` зазвичай не змінюються
    після створення, або змінюються через спеціальні процедури.
    Якщо потрібно їх змінювати, ці поля можна додати сюди як Optional.
    """
    value: Optional[Any] = Field(None, description="Нове значення налаштування")
    # description: Optional[str] = Field(None, description="Новий опис") # Якщо опис можна змінювати
    # is_editable: Optional[bool] = Field(None, description="Зміна можливості редагування") # Якщо можна змінювати

    # Валідатор для `value` тут також потрібен, АЛЕ він має знати `value_type`
    # існуючого запису в БД, щоб правильно валідувати та серіалізувати.
    # Це означає, що `value_type` має бути або переданий в схему,
    # або отриманий з БД перед валідацією.
    #
    # Якщо `value_type` не змінюється, то при оновленні ми маємо його знати.
    # Тому, `SystemSettingUpdateSchema` може потребувати `value_type` з контексту.
    # Або ж, якщо API ендпоінт для оновлення приймає лише `value`,
    # то він сам має отримати `value_type` з БД і виконати валідацію/серіалізацію.
    #
    # Для простоти, припустимо, що ендпоінт оновлення отримує `value_type` з існуючого запису
    # і використовує логіку, схожу на валідатор в `SystemSettingCreateSchema`,
    # для перевірки та серіалізації нового `value`.
    # Тому тут `SystemSettingUpdateSchema` може бути простою.
    #
    # Якщо ж ми хочемо, щоб схема сама валідувала, то вона має бути складнішою:
    # @model_validator(mode='before') # Або 'after', залежно від того, як дані надходять
    # def validate_and_serialize_update_value(cls, data: Any, **kwargs) -> Any:
    #     # Потрібен доступ до `value_type` існуючого об'єкта
    #     # Це зазвичай робиться в сервісному шарі або в самому ендпоінті.
    #     # Схема сама по собі не має доступу до стану БД.
    #     # Тому цей валідатор тут не дуже практичний без додаткового контексту.
    #     # ... логіка валідації та серіалізації ...
    #     return data
    #
    # Тому, для `UpdateSchema`, валідація/серіалізація `value` на основі `value_type`
    # має відбуватися в логіці ендпоінта/сервісу, який має доступ до `value_type`
    # існуючого налаштування.
    # Схема тут лише визначає, що `value` може бути передано.
    pass


# TODO: Переконатися, що схеми відповідають моделі `SystemSettingModel`.
# `SystemSettingModel` має `id, key, value (Text), value_type, description, is_editable, created_at, updated_at`.
# `SystemSettingSchema` відображає ці поля, з автоматичним розпарсингом `value` на основі `value_type`.
# `SystemSettingCreateSchema` включає необхідні поля для створення, з валідацією `key` та `value_type`,
# а також валідацією та серіалізацією `value` в рядок.
# `SystemSettingUpdateSchema` дозволяє оновлювати `value`.
# Це виглядає узгоджено.
# Важливо, що `SystemSettingModel.value` зберігається як `Text`, тому схеми `Create` та `Update`
# повинні забезпечувати серіалізацію значення в рядок перед збереженням,
# а схема `Read` (SystemSettingSchema) - десеріалізацію з рядка в потрібний тип.
# Валідатор `convert_value_from_string` в `SystemSettingSchema` робить десеріалізацію.
# Валідатор `validate_value_against_type_and_serialize` в `SystemSettingCreateSchema` робить валідацію типу та серіалізацію в рядок.
# Для `SystemSettingUpdateSchema` логіка валідації/серіалізації `value` винесена на сервісний рівень.
# Це прийнятний підхід.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# Все виглядає коректно.

SystemSettingSchema.model_rebuild()
SystemSettingCreateSchema.model_rebuild()
SystemSettingUpdateSchema.model_rebuild()
