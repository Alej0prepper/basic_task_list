#!/usr/bin/env bash
set -euo pipefail

echo "== 1) APAGAR Y LIMPIAR DOCKER =="
docker compose down --remove-orphans || true

# Borra contenedores huérfanos por si quedaron (ajusta nombres si difieren)
docker rm -f tasklist-backend-app-1 tasklist-backend-db-1 tasklist-backend-app-test-1 2>/dev/null || true

# Borra volumen de datos (¡datos de Postgres desaparecen!)
docker volume rm tasklist-backend_db_data 2>/dev/null || true

# Borra red del compose (por si quedó)
docker network rm tasklist-backend_default 2>/dev/null || true

# Borra imágenes locales de la app para evitar migraciones "horneadas"
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | awk '/tasklist|backend|app/ {print $2}' | xargs -r docker rmi -f || true

# Limpia cache de builder (opcional pero recomendable)
docker builder prune -f || true

echo "== 2) LIMPIEZA DEL REPO =="
# Limpia migraciones y caches locales
rm -rf alembic/versions/* .pytest_cache __pycache__ **/__pycache__ /tmp/validate_uvicorn.log 2>/dev/null || true
mkdir -p alembic/versions

# (Opcional) limpia venv si quieres arrancar también limpio en local
# rm -rf .venv

echo "== 3) VALIDAR .env (host=db en la URL!) =="
# Asegúrate de tener DATABASE_URL apuntando al servicio 'db'
# Si no existe .env, creamos uno mínimo correcto:
if ! grep -q '^DATABASE_URL=' .env 2>/dev/null; then
  cat > .env <<'ENV'
POSTGRES_DB=tasklist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/tasklist
APP_PORT=8012
APP_ENV=prod
SECRET_KEY=un_secreto_largo_y_aleatorio
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ENV
  echo "[.env] creado"
else
  echo "[.env] encontrado; verifica que DATABASE_URL use host db, NO localhost"
fi

echo "== 4) SUBIR SOLO LA DB =="
docker compose up -d db

echo "== 5) CREAR HEAD 'VACÍO' PARA BOOTSTRAP (evita 'Target database is not up to date') =="
# Vacía las versiones dentro del contenedor y crea head vacío
docker compose run --rm app bash -lc 'rm -rf alembic/versions/*; mkdir -p alembic/versions && ls -la alembic/versions'
docker compose run --rm app alembic stamp base
docker compose run --rm app alembic revision -m "bootstrap empty"
docker compose run --rm app alembic upgrade head

echo "== 6) GENERAR ESQUEMA REAL (AUTOGENERATE) Y APLICAR =="
# MUY IMPORTANTE: env.py debe importar Base y modelos.
# from tasklist_app.database import Base
# from tasklist_app import models
# target_metadata = Base.metadata
docker compose run --rm app alembic revision --autogenerate -m "initial fresh schema"
docker compose run --rm app alembic upgrade head

echo "== 7) VER TABLAS EN POSTGRES =="
docker compose exec db psql -U postgres -d tasklist -c "\dt"
docker compose exec db psql -U postgres -d tasklist -c "\d+ tasks" || true
docker compose exec db psql -U postgres -d tasklist -c "\d+ users" || true

echo "== 8) ARRANCAR LA APP =="
docker compose up -d app
docker compose logs -f app | sed -n '1,120p'

echo "== DONE =="
