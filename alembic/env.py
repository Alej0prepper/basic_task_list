from __future__ import annotations


import sys, pathlib, os
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from logging.config import fileConfig
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

load_dotenv()  

from tasklist_app.database import Base
from tasklist_app import models  


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Modo offline: construye SQL sin conexión."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está definido en el entorno.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Modo online: usa una conexión real."""
    # lee la sección [alembic] de alembic.ini y SOBRESCRIBE la URL con la env var
    configuration = config.get_section(config.config_ini_section)
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está definido en el entorno.")
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Carga DATABASE_URL del entorno
config = context.config
if url := os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", url)

# 2) target_metadata = Base.metadata y asegurarse de importar modelos
from tasklist_app.database import Base
from tasklist_app import models  # <- imprescindible para autogenerate
target_metadata = Base.metadata