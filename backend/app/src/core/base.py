# backend/app/src/core/base.py

"""
Цей модуль може містити базові класи або основні утиліти, які є фундаментальними
для структури програми, але не вписуються у більш специфічні файли `base.py`
(наприклад, `models.base`, `repositories.base`).

Наразі цей модуль може бути мінімальним. Його можна розширити, якщо будуть виявлені
справді загальні, не пов'язані з доменом базові функціональності для компонентів,
таких як сервіси або інші основні утиліти.
"""

from typing import TypeVar, Generic, Any, Dict
from pydantic import BaseModel

# Загальні TypeVariable для моделей Pydantic, корисні для базових шаблонів сервісів/репозиторіїв
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Приклад дуже загального базового класу, який може використовуватися іншими компонентами.
# Однак, специфічні базові класи для сервісів або репозиторіїв часто краще розміщувати
# у відповідних модулях (наприклад, `services/base.py`, `repositories/base.py`),
# щоб розділити відповідальності та дозволити доменно-специфічні базові функціональності.

class BaseCoreComponent:
    """
    Приклад дуже загального базового компонента.
    Його корисність залежатиме від загальних, не пов'язаних з доменом методів,
    необхідних у різних основних частинах програми.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Заповнювач для загальної логіки ініціалізації, якщо така є
        pass

    def get_component_name(self) -> str:
        """Повертає назву класу компонента."""
        return self.__class__.__name__

# Приклад простого класу-утиліти, який міг би знаходитися тут, якби він був фундаментальним
# і використовувався багатьма основними компонентами.

class ObjectConfigurator:
    """
    Клас-утиліта для допомоги в налаштуванні об'єктів зі словників.
    Це концептуальний приклад; моделі Pydantic зазвичай обробляють це для об'єктів даних.
    """
    @staticmethod
    def configure_from_dict(obj: Any, config_dict: Dict[str, Any]) -> None:
        """
        Налаштовує атрибути об'єкта зі словника.

        Args:
            obj: Об'єкт для налаштування.
            config_dict: Словник, де ключі відповідають назвам атрибутів.
        """
        for key, value in config_dict.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                # Опціонально логувати попередження або викликати помилку для невідомих ключів
                # print(f"Попередження: Атрибут '{key}' не знайдено в об'єкті {obj.__class__.__name__}")
                pass

if __name__ == "__main__":
    print("--- Основні базові компоненти/утиліти ---")

    core_comp = BaseCoreComponent()
    print(f"Назва компонента: {core_comp.get_component_name()}")

    class MyTestObject:
        def __init__(self):
            self.name: str = "DefaultName"
            self.value: int = 0

    test_obj = MyTestObject()
    print(f"До налаштування: Ім'я='{test_obj.name}', Значення={test_obj.value}")

    config_data = {"name": "ConfiguredName", "value": 100, "non_existent_attr": "test"}
    ObjectConfigurator.configure_from_dict(test_obj, config_data)
    print(f"Після налаштування: Ім'я='{test_obj.name}', Значення={test_obj.value}")
    # Примітка: 'non_existent_attr' буде проігноровано або видасть попередження залежно від реалізації

    print("\nTypeVars, визначені для моделей Pydantic (для використання в загальних базових класах):")
    print(f"ModelType: {ModelType}")
    print(f"CreateSchemaType: {CreateSchemaType}")
    print(f"UpdateSchemaType: {UpdateSchemaType}")
