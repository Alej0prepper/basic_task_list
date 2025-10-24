FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# deps del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl jq \
  && rm -rf /var/lib/apt/lists/*

# copiar código (tus líneas como ya las tenías)
COPY tasklist_app /app/tasklist_app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY entrypoint.sh /app/entrypoint.sh
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini

# deps de Python (añadimos pytest + plugin)
RUN python -m pip install --upgrade pip \
  && pip install fastapi uvicorn[standard] SQLAlchemy psycopg2-binary python-dotenv pydantic alembic sqladmin \
               pytest httpx pytest-json-report

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
