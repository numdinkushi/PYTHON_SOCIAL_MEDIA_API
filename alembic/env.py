from app.config import settings  # pylint: disable=import-error
from app import models  # pylint: disable=import-error,unused-import
from app.models import Base  # pylint: disable=import-error
from app.database import build_database_url  # pylint: disable=import-error
from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context  # pylint: disable=import-error

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config  # pylint: disable=no-member

# Override sqlalchemy.url from config to use the same settings as database.py
# This ensures SSL configuration is properly applied for Render PostgreSQL
database_url = build_database_url()
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(  # pylint: disable=no-member
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():  # pylint: disable=no-member
        context.run_migrations()  # pylint: disable=no-member


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Build connection arguments for SSL configuration (required for Render PostgreSQL)
    connect_args = {}
    if "render.com" in database_url.lower():
        connect_args = {
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 10,
        }
    
    configuration = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(  # pylint: disable=no-member
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():  # pylint: disable=no-member
            context.run_migrations()  # pylint: disable=no-member


if context.is_offline_mode():  # type: ignore # pylint: disable=no-member
    run_migrations_offline()
else:
    run_migrations_online()
