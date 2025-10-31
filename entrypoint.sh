#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "[entrypoint] 🚀 Starting TaskList backend"
echo "============================================================"
echo "[entrypoint] DATABASE_URL=${DATABASE_URL}"
echo "[entrypoint] Waiting for PostgreSQL at db:5432..."

# ------------------------------------------------------------
# 🕒 Esperar a que PostgreSQL esté listo
# ------------------------------------------------------------
until nc -z -v -w30 db 5432; do
  echo "[entrypoint] ⏳ waiting for db..."
  sleep 1
done

echo "[entrypoint] ✅ PostgreSQL is up!"

# ------------------------------------------------------------
# 📜 Migraciones Alembic
# ------------------------------------------------------------
echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head
echo "[entrypoint] ✅ Alembic migrations applied!"

# ------------------------------------------------------------
# 🌐 Configurar Ngrok si existe token
# ------------------------------------------------------------
if [ -n "${NGROK_AUTHTOKEN:-}" ]; then
  echo "[entrypoint] 🔐 Configuring Ngrok authtoken..."
  ngrok config add-authtoken "${NGROK_AUTHTOKEN}"
else
  echo "[entrypoint] ⚠️ No NGROK_AUTHTOKEN provided, using anonymous session."
fi

# ------------------------------------------------------------
# 🚀 Iniciar Ngrok en segundo plano
# ------------------------------------------------------------
echo "[entrypoint] Starting Ngrok tunnel on port 8000..."
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &

# Esperar un momento a que arranque
sleep 3

# ------------------------------------------------------------
# 🔍 Capturar y guardar la URL pública de Ngrok
# ------------------------------------------------------------
NGROK_URL=$(grep -m1 -oE "https://[0-9a-z-]+\.ngrok-[a-z]+\.app" /tmp/ngrok.log || true)
if [ -n "${NGROK_URL}" ]; then
  echo "[entrypoint] 🌍 Public URL: ${NGROK_URL}"
  echo "${NGROK_URL}" > /app/.ngrok-url
else
  echo "[entrypoint] ⚠️ Could not extract Ngrok URL yet. It will appear in logs soon."
fi

# ------------------------------------------------------------
# 🧠 Lanzar la aplicación FastAPI (Uvicorn)
# ------------------------------------------------------------
echo "[entrypoint] Starting Uvicorn server..."
exec uvicorn tasklist_app.main:app --host 0.0.0.0 --port 8000
