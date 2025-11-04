#!/usr/bin/env bash
set -euo pipefail

log()  { printf "%s %s\n" "[entrypoint]" "$*" >&1; }
err()  { printf "%s %s\n" "[entrypoint][ERR]" "$*" >&2; }
has()  { command -v "$1" >/dev/null 2>&1; }

log "============================================================"
log "🚀 Starting TaskList backend (diagnostic edition)"
log "============================================================"

# -------------------------------------------------------------------
# 0) Variables esperadas
# -------------------------------------------------------------------
: "${DATABASE_URL:?DATABASE_URL is required, e.g. postgresql+psycopg2://postgres:postgres@db:5432/tasklist}"

# -------------------------------------------------------------------
# 1) Parsear DATABASE_URL
#     Formatos soportados: postgresql+psycopg2://user:pass@host:port/db
# -------------------------------------------------------------------
URL_NO_DRIVER="${DATABASE_URL#postgresql+psycopg2://}"
DB_USER="${URL_NO_DRIVER%%:*}";        REST="${URL_NO_DRIVER#*:}"
DB_PASS="${REST%%@*}";                 REST="${REST#*@}"
DB_HOST="${REST%%:*}";                 REST="${REST#*:}"
DB_PORT="${REST%%/*}";                 DB_NAME="${REST#*/}"

# Validación básica
if [[ -z "$DB_USER" || -z "$DB_PASS" || -z "$DB_HOST" || -z "$DB_PORT" || -z "$DB_NAME" ]]; then
  err "DATABASE_URL mal formateada. Recibí:"
  err "  DATABASE_URL=$DATABASE_URL"
  err "Esperaba: postgresql+psycopg2://user:pass@host:port/dbname"
  exit 1
fi

log "🔧 Parsed DATABASE_URL:"
log "   host=$DB_HOST port=$DB_PORT db=$DB_NAME user=$DB_USER (password: $( [ -n "$DB_PASS" ] && echo '******' || echo '<empty>' ))"
log "✅ Trying to connect to database '$DB_NAME' as user '$DB_USER'."

# -------------------------------------------------------------------
# 2) Comprobación de puerto TCP
# -------------------------------------------------------------------
if has nc; then
  tries_tcp=0
  until nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; do
    tries_tcp=$((tries_tcp+1))
    if [ "$tries_tcp" -ge 30 ]; then
      err "No TCP connectivity to $DB_HOST:$DB_PORT after 60s (is the 'db' service up? network/compose?)."
      exit 1
    fi
    sleep 2
  done
  log "🌐 TCP port open at $DB_HOST:$DB_PORT."
else
  log "ℹ️ 'nc' not found; skipping raw TCP check."
fi

# -------------------------------------------------------------------
# 3) pg_isready (si existe)
# -------------------------------------------------------------------
if has pg_isready; then
  tries_ready=0
  until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    tries_ready=$((tries_ready+1))
    if [ "$tries_ready" -ge 30 ]; then
      err "pg_isready no reporta listo tras 60s para $DB_HOST:$DB_PORT db=$DB_NAME user=$DB_USER."
      err "Suele ser: base no creada aún, credenciales inválidas, o HBA."
      break
    fi
    sleep 2
  done
  if [ "$tries_ready" -lt 30 ]; then
    log "🟢 pg_isready: OK para $DB_NAME."
  fi
else
  log "ℹ️ 'pg_isready' no está instalado; continuamos."
fi

# -------------------------------------------------------------------
# 4) psql SELECT 1 con diagnóstico de error
# -------------------------------------------------------------------
psql_ok=0
if has psql; then
  # Intento con salida detallada de error
  if PGPASSWORD="$DB_PASS" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME" -v ON_ERROR_STOP=1 -c "SELECT 1;" >/dev/null 2>"/tmp/psql.err"; then
    psql_ok=1
    log "✅ SELECT 1 OK en '$DB_NAME'."
  else
    err "❌ Falló SELECT 1 contra '$DB_NAME'. Error devuelto por psql:"
    sed 's/^/[psql] /' </tmp/psql.err >&2

    # Diagnósticos adicionales útiles
    err "🔎 Comprobando si el servidor responde y qué DBs existen (no requiere superusuario):"
    # Lista de DBs visibles
    PGPASSWORD="$DB_PASS" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/postgres" -c "SELECT datname FROM pg_database ORDER BY 1;" 2>&1 | sed 's/^/[psql] /' || true

    err "🔎 Probando autenticar al sistema 'postgres' con consulta simple:"
    PGPASSWORD="$DB_PASS" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/postgres" -c "SELECT current_user, version();" 2>&1 | sed 's/^/[psql] /' || true
  fi
else
  err "⚠️ 'psql' no está instalado en este contenedor. Instálalo para diagnóstico detallado:"
  err "    apt-get update && apt-get install -y --no-install-recommends postgresql-client"
fi

# Si no pasó psql y existe psql, fallar (no seguimos a ciegas)
if has psql && [ "$psql_ok" -ne 1 ]; then
  err "Abortando arranque: la conexión a '$DB_NAME' no está OK. Revisa el error de psql arriba."
  exit 1
fi

# -------------------------------------------------------------------
# 5) Migraciones Alembic
# -------------------------------------------------------------------
log "📜 Running Alembic migrations..."
alembic upgrade head
log "✅ Alembic migrations applied!"

# -------------------------------------------------------------------
# 6) Ngrok
# -------------------------------------------------------------------
# 🌐 Configurar Ngrok si existe token
if [ -n "${NGROK_AUTHTOKEN:-}" ]; then
  echo "[entrypoint] 🔐 Configuring Ngrok authtoken..."
  ngrok config add-authtoken "${NGROK_AUTHTOKEN}"
else
  echo "[entrypoint] ⚠️ No NGROK_AUTHTOKEN provided, using anonymous session."
fi

# 🚀 Iniciar Ngrok en segundo plano
echo "[entrypoint] Starting Ngrok tunnel on port 8000..."
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &

sleep 3
# -------------------------------------------------------------------
# 7) Lanzar la app
# -------------------------------------------------------------------
log "🚀 Starting Uvicorn server..."
exec uvicorn tasklist_app.main:app --host 0.0.0.0 --port 8000
