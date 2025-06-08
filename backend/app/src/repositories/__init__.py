# backend/app/src/repositories/__init__.py
from .base import BaseRepository

# This line exports the BaseRepository class when the package is imported,
# making it available as `from app.src.repositories import BaseRepository`.

# When you create specific repositories, you will import and export them here
# to make them easily accessible from the repositories package.
# For example:
# from .user_repository import UserRepository
# from .item_repository import ItemRepository
#
# __all__ = [
#     "BaseRepository",
#     "UserRepository",
#     "ItemRepository",
#     # Add other repository class names here
# ]

# For now, only BaseRepository is defined.
__all__ = [
    "BaseRepository",
]

# Detailed comments:
# This __init__.py file serves two main purposes within the 'repositories' package:
#
# 1. Package Initialization:
#    It signals to Python that the 'repositories' directory should be treated as a
#    package (or sub-package). This allows you to organize your repository-related
#    modules within this directory and import them using dot notation.
#
# 2. Convenient Imports:
#    By importing and re-exporting classes like `BaseRepository` (and later,
#    specific repositories like `UserRepository`), this file provides a cleaner
#    and more convenient API for other parts of your application to access these
#    classes. Instead of needing to know the exact module file where a class is
#    defined (e.g., `from app.src.repositories.base import BaseRepository`),
#    other modules can simply use:
#    `from app.src.repositories import BaseRepository`.
#
# 3. Controlling `import *`:
#    The `__all__` list defines the public API of this package when a client uses
#    `from app.src.repositories import *`. Only names listed in `__all__` will be
#    imported with a wildcard import. This helps to prevent namespace pollution
#    and makes it clear which components are intended for external use.
#    As you add more repositories (e.g., UserRepository, GroupRepository),
#    you should add their class names to the `__all__` list.
#
# Future Expansion:
# As the application grows, you will create more specific repository classes
# (e.g., `user_repository.py`, `task_repository.py`). Each of those new
# repository classes should be imported into this `__init__.py` file and
# added to the `__all__` list. This keeps the import structure consistent
# and manageable.
#
# Example of adding a new repository:
#
# 1. Create `user_repository.py` in the `repositories` directory:
#    ```python
#    # backend/app/src/repositories/user_repository.py
#    from .base import BaseRepository
#    from app.src.models.auth.user import User  # Assuming User model path
#    from app.src.schemas.auth.user import UserCreate, UserUpdate # Assuming User schemas
#
#    class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
#        def __init__(self):
#            super().__init__(User)
#        # ... user-specific methods
#    ```
#
# 2. Update `__init__.py` in the `repositories` directory:
#    ```python
#    # backend/app/src/repositories/__init__.py
#    from .base import BaseRepository
#    from .user_repository import UserRepository # Import the new repository
#
#    __all__ = [
#        "BaseRepository",
#        "UserRepository", # Add to __all__
#    ]
#    ```
#
# This setup promotes a clean and organized structure for your data access layer.
