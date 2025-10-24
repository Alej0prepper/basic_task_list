#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] DATABASE_URL=${DATABASE_URL:-<not-set>}"

# Espera a Postgres si la URL es postgres
if [[ "${DATABASE_URL:-}" == postgresql* ]]; then
  echo "[entrypoint] waiting for postgres..."
  # Extrae host y puerto de la URL (formato básico)
  DB_HOST=$(python - <<'PY'
import os, re
url=os.environ.get("DATABASE_URL","")
m=re.match(r"^.+://.+:(.+)@([^:/]+):(\d+)/.+$", url)
print(m.group(2) if m else "db")
PY
)
  DB_PORT=$(python - <<'PY'
import os, re
url=os.environ.get("DATABASE_URL","")
m=re.match(r"^.+://.+:(.+)@([^:/]+):(\d+)/.+$", url)
print(m.group(3) if m else "5432")
PY
)
  # poll con netcat si está disponible, si no curl con timeout
  for i in $(seq 1 60); do
    if (echo > /dev/tcp/$DB_HOST/$DB_PORT) >/dev/null 2>&1; then
      echo "[entrypoint] postgres is up"
      break
    fi
    echo "[entrypoint] waiting ($i/60) for ${DB_HOST}:${DB_PORT}..."
    sleep 1
  done
fi

# Migraciones
echo "[entrypoint] running alembic upgrade head..."
PYTHONPATH=/app alembic upgrade head

# Arranca API
echo "[entrypoint] starting uvicorn..."
exec uvicorn tasklist_app.main:app --host 0.0.0.0 --port 8000
