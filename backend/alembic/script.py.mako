## backend/alembic/script.py.mako
## -*- coding: utf-8 -*-
"""Шаблон Mako для генерації скриптів міграцій Alembic.

Цей файл є шаблоном, який Alembic використовує для створення нових
файлів ревізій міграцій за допомогою команди `alembic revision`.
Він визначає базову структуру кожного файлу міграції, включаючи
необхідні імпорти (Alembic, SQLAlchemy), змінні для ідентифікаторів
ревізій (`revision`, `down_revision`) та порожні функції `upgrade()`
і `downgrade()`, які розробник заповнює командами для зміни схеми БД.
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Ідентифікатори ревізій, що використовуються Alembic для керування послідовністю міграцій.
# revision: Унікальний ідентифікатор поточної ревізії (генерується Alembic).
# down_revision: Ідентифікатор попередньої ревізії (батьківської), від якої залежить ця міграція.
# branch_labels: Мітки гілок, якщо в проекті використовуються іменовані гілки міграцій.
# depends_on: Список ідентифікаторів ревізій з інших гілок, від яких залежить ця міграція.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Застосовує зміни до схеми бази даних (перехід "вперед").

    Ця функція викликається, коли Alembic застосовує міграцію.
    Сюди слід додавати команди Alembic `op.*` для створення таблиць,
    додавання колонок, створення індексів, обмежень тощо.

    Приклад створення таблиці:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )
    """
    ${upgrades if upgrades else "# ### Команди, автоматично згенеровані Alembic - будь ласка, відредагуйте! ###\n    pass\n    # ### Кінець команд Alembic ###"}


def downgrade() -> None:
    """Відкочує зміни схеми бази даних (перехід "назад").

    Ця функція викликається, коли Alembic відкочує міграцію.
    Сюди слід додавати команди Alembic `op.*` для видалення таблиць,
    колонок, індексів тощо, які були створені у відповідній функції `upgrade()`.
    Важливо забезпечити, щоб `downgrade()` виконував дії, обернені до `upgrade()`.

    Приклад видалення таблиці:
    op.drop_table('users')
    """
    ${downgrades if downgrades else "# ### Команди, автоматично згенеровані Alembic - будь ласка, відредагуйте! ###\n    pass\n    # ### Кінець команд Alembic ###"}
