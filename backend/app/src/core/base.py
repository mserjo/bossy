# backend/app/src/core/base.py

"""
This module can contain base classes or core utilities that are fundamental
to the application's structure but don't fit into more specific `base.py` files
(e.g., `models.base`, `repositories.base`).

For now, this might be minimal. It can be expanded if truly generic, non-domain-specific
base functionalities are identified for components like services or other core utilities.
"""

from typing import TypeVar, Generic, Any, Dict
from pydantic import BaseModel

# Generic TypeVariable for Pydantic models, useful for base service/repository patterns
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Example of a very generic base class that might be used by other components.
# However, specific base classes for services or repositories are often better placed
# in their respective modules (e.g., `services/base.py`, `repositories/base.py`)
# to keep concerns separated and allow for domain-specific base functionalities.

class BaseCoreComponent:
    """
    An example of a very generic base component.
    Its utility would depend on common, non-domain-specific methods needed across
    various core parts of the application.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Placeholder for common initialization logic if any
        pass

    def get_component_name(self) -> str:
        """Returns the name of the component class."""
        return self.__class__.__name__

# Example of a simple utility class that could reside here if it's fundamental
# and used by many core components.

class ObjectConfigurator:
    """
    A utility class to help configure objects from dictionaries.
    This is a conceptual example; Pydantic models usually handle this for data objects.
    """
    @staticmethod
    def configure_from_dict(obj: Any, config_dict: Dict[str, Any]) -> None:
        """
        Configures an object's attributes from a dictionary.

        Args:
            obj: The object to configure.
            config_dict: A dictionary where keys correspond to attribute names.
        """
        for key, value in config_dict.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                # Optionally log a warning or raise an error for unknown keys
                # print(f"Warning: Attribute '{key}' not found on object {obj.__class__.__name__}")
                pass

if __name__ == "__main__":
    print("--- Core Base Components/Utilities ---")

    core_comp = BaseCoreComponent()
    print(f"Component Name: {core_comp.get_component_name()}")

    class MyTestObject:
        def __init__(self):
            self.name: str = "DefaultName"
            self.value: int = 0

    test_obj = MyTestObject()
    print(f"Before configuration: Name='{test_obj.name}', Value={test_obj.value}")

    config_data = {"name": "ConfiguredName", "value": 100, "non_existent_attr": "test"}
    ObjectConfigurator.configure_from_dict(test_obj, config_data)
    print(f"After configuration: Name='{test_obj.name}', Value={test_obj.value}")
    # Note: 'non_existent_attr' would be ignored or warned based on implementation

    print("\nTypeVars defined for Pydantic models (for use in generic base classes):")
    print(f"ModelType: {ModelType}")
    print(f"CreateSchemaType: {CreateSchemaType}")
    print(f"UpdateSchemaType: {UpdateSchemaType}")
