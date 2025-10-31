#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------
# validate.sh — Validaciones pasos 2–5 (WSL)
# -----------------------------------------------
# Checks:
#  1) Estructura del proyecto y __init__.py
#  2) Imports de módulos (database, schemas, models, utils, deps, crud, main)
#  3) Alembic: env, path, versions y (opcional) upgrade
#  4) DB: conexión y existencia de tabla 'tasks'
#  5) API: levantar uvicorn en puerto dado y hacer smoke test (si tabla existe)
#
# Flags:
#   --migrate       : corre 'alembic upgrade head' si hay migraciones
#   --use-sqlite    : exporta DATABASE_URL=sqlite+pysqlite:///./dev.db (ignora .env)
#   --port <PUERTO> : puerto para la prueba de API (default 8011)
#
# Requisitos: python3, pip, uvicorn, alembic, docker (solo si usas Postgres por Docker)
# -----------------------------------------------

# ---------- args ----------
MIGRATE=false
FORCE_SQLITE=false
PORT=8011

while [[ $# -gt 0 ]]; do
  case "$1" in
    --migrate) MIGRATE=true; shift ;;
    --use-sqlite) FORCE_SQLITE=true; shift ;;
    --port) PORT="${2:-8011}"; shift 2 ;;
    *) echo "Flag desconocida: $1"; exit 1 ;;
  esac
done

# ---------- helpers ----------
c_ok(){ printf "\033[32m%s\033[0m\n" "$*"; }
c_warn(){ printf "\033[33m%s\033[0m\n" "$*"; }
c_err(){ printf "\033[31m%s\033[0m\n" "$*"; }
c_info(){ printf "\033[36m%s\033[0m\n" "$*"; }

die(){ c_err "ERROR: $*"; exit 1; }

# ---------- 0) ubicación ----------
ROOT="$(pwd)"
[ -f "${ROOT}/alembic.ini" ] || die "No encuentro alembic.ini en $(pwd). Ejecuta el script desde la RAÍZ del proyecto."
[ -d "${ROOT}/tasklist_app" ] || die "No existe carpeta tasklist_app/ en $(pwd)."

# ---------- 1) estructura ----------
c_info "1) Validando estructura del proyecto…"
[ -f tasklist_app/__init__.py ] || die "Falta tasklist_app/__init__.py"
for f in database.py models.py schemas.py utils.py deps.py crud.py main.py; do
  [ -f "tasklist_app/$f" ] || die "Falta tasklist_app/$f"
done
c_ok "✔ Estructura OK"

# ---------- 2) comandos requeridos ----------
c_info "2) Verificando binarios requeridos…"
command -v python3 >/dev/null || die "python3 no instalado"
command -v pip >/dev/null || die "pip no instalado"
command -v uvicorn >/dev/null || c_warn "uvicorn no encontrado en PATH (lo usaré vía 'python3 -m uvicorn')"
command -v alembic >/dev/null || die "alembic no instalado (pip install alembic)"
c_ok "✔ Binarios base OK"

# ---------- 3) cargar .env si existe ----------
if $FORCE_SQLITE; then
  export DATABASE_URL="sqlite+pysqlite:///./dev.db"
  c_warn "Forzando DATABASE_URL a SQLite: ${DATABASE_URL}"
else
  if [ -f .env ]; then
    # shellcheck disable=SC2046
    export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env | xargs) || true
    c_ok "✔ .env cargado"
  else
    c_warn "No hay .env; usaré DATABASE_URL=${DATABASE_URL:-'(no definido)'}"
  fi
fi

# ---------- 4) imports de módulos ----------
c_info "3) Validando imports de módulos…"
python3 - << 'PY'
import sys, os, importlib, inspect
sys.path.insert(0, os.getcwd())

modules = [
  "tasklist_app",
  "tasklist_app.database",
  "tasklist_app.schemas",
  "tasklist_app.models",
  "tasklist_app.utils",
  "tasklist_app.deps",
  "tasklist_app.crud",
  "tasklist_app.main",
]

for m in modules:
  mod = importlib.import_module(m)
  fn = getattr(mod, "__file__", None)
  print(f"✔ import {m} -> {fn}")

# Imprime rutas de la API para ver que estén
from tasklist_app.main import app
paths = []
for r in app.routes:
    p = getattr(r, "path", None)
    if p:
        methods = sorted(list(getattr(r, "methods", [])))
        paths.append((p, methods))
print("✔ rutas:", paths)
PY
c_ok "✔ Imports OK"

# ---------- 5) Alembic: path y metadata ----------
c_info "4) Validando Alembic y metadata…"
python3 - << 'PY'
import sys, os, importlib, inspect
sys.path.insert(0, os.getcwd())
from sqlalchemy import create_engine, inspect as sqinspect
from tasklist_app.database import DATABASE_URL
print("DB URL:", DATABASE_URL)
PY

# Heads existentes (si falla, al menos muestra diagnóstico)
if ! PYTHONPATH=. alembic heads >/dev/null 2>&1; then
  c_warn "No se pudo listar 'alembic heads'. Revisa alembic/env.py (sys.path, imports, load_dotenv)."
else
  c_ok "✔ Alembic accesible (heads listado OK)"
fi

# ---------- 6) DB: conexión y tabla 'tasks' ----------
c_info "5) Comprobando conexión y existencia de tabla 'tasks'…"
python3 - << 'PY'
import sys, os
from sqlalchemy import create_engine
from tasklist_app.database import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
with engine.connect() as conn:
    conn.exec_driver_sql("SELECT 1")
print("✅ Conexión OK")
PY


# ---------- 7) migrar si se pidió ----------
if $MIGRATE; then
  c_info "6) Ejecutando alembic upgrade head (por --migrate)…"
  PYTHONPATH=. alembic upgrade head || die "alembic upgrade head falló"
  c_ok "✔ Migración aplicada"
  # Rechequear tabla
  python3 - << 'PY'
import sys, os
sys.path.insert(0, os.getcwd())
from sqlalchemy import create_engine, inspect
from tasklist_app.database import DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
inspector = inspect(engine)
print("✔ Tabla 'tasks' existe ahora?:", inspector.has_table("tasks"))
PY
else
  c_warn "No se ejecuta migrate (use --migrate si quieres 'alembic upgrade head')."
fi

# ---------- 8) API smoke test (solo si existe tabla) ----------
c_info "7) Smoke test de API (si existe tabla 'tasks')…"
HAS_TASKS="$(python3 - << 'PY'
import sys, os
sys.path.insert(0, os.getcwd())
from sqlalchemy import create_engine, inspect
from tasklist_app.database import DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
print( 'yes' if inspect(engine).has_table('tasks') else 'no' )
PY
)"

if [ "$HAS_TASKS" = "yes" ]; then
  c_info "• Levantando API temporal en :$PORT"
  # Arranca en background
  ( DATABASE_URL="${DATABASE_URL:-}" python3 -m uvicorn --app-dir "$(pwd)" tasklist_app.main:app --host 0.0.0.0 --port "$PORT" >/tmp/validate_uvicorn.log 2>&1 ) &
  UV_PID=$!
  sleep 2

  # Health
  if curl -s "http://127.0.0.1:${PORT}/health" | grep -q '"ok"'; then
    c_ok "✔ /health OK"
  else
    c_warn "No respondió /health correctamente. Revisa /tmp/validate_uvicorn.log"
  fi

  # CRUD mínimo: crear y listar
  CREATE_STATUS="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/tasks" \
    -H "Content-Type: application/json" \
    -d '{"text":"hola @dev #tag test@gmail.com https://example.com","status":"pending"}')"

  if [ "$CREATE_STATUS" = "201" ]; then
    c_ok "✔ POST /tasks (201)"
  else
    c_warn "POST /tasks devolvió ${CREATE_STATUS}. Puede faltar esquema o falló DB. Ver /tmp/validate_uvicorn.log"
  fi

  LIST_STATUS="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/tasks")"
  if [ "$LIST_STATUS" = "200" ]; then
    c_ok "✔ GET /tasks (200)"
  else
    c_warn "GET /tasks devolvió ${LIST_STATUS}. Ver /tmp/validate_uvicorn.log"
  fi

  # parar server
  kill "$UV_PID" >/dev/null 2>&1 || true
else
  c_warn "Saltando smoke test de API: no existe la tabla 'tasks'. Ejecuta './validate.sh --migrate' primero."
fi

c_ok "✅ Validaciones finalizadas."
python3 - << 'PY'
import sys, os
from sqlalchemy import create_engine
from tasklist_app.database import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
with engine.connect() as conn:
    conn.exec_driver_sql("SELECT 1")
print("✅ Conexión OK")
PY
