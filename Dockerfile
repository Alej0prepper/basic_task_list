# ---------- Base ----------
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# No generar archivos .pyc y mostrar logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Puerto de la aplicación
ENV PORT=8000

# ---------- Sistema base ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl netcat-openbsd gnupg sudo \
  && rm -rf /var/lib/apt/lists/*

# ---------- Instalar Ngrok ----------
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | tee /etc/apt/sources.list.d/ngrok.list \
  && apt-get update && apt-get install -y ngrok \
  && rm -rf /var/lib/apt/lists/*

# ---------- Copia del código ----------
COPY tasklist_app /app/tasklist_app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
# ---------- Dependencias Python ----------
RUN python -m pip install --upgrade pip && \
    pip install \
      fastapi \
      uvicorn[standard] \
      SQLAlchemy \
      psycopg2-binary \
      python-dotenv \
      pydantic \
      "pydantic[email]" \
      pydantic-settings \
      alembic \
      sqladmin \
      "python-jose[cryptography]" \
      passlib==1.7.4 "passlib[bcrypt]" \
      bcrypt==3.2.2 \
      pytest pytest-cov pytest-asyncio httpx \
      openpyxl>=3.1.2 itsdangerous python-multipart
# ---------- Permisos ----------
RUN chmod +x /app/entrypoint.sh

# ---------- Exponer puerto ----------
EXPOSE 8000

# ---------- Comando de ejecución ----------
# Ejecuta tu app y Ngrok en paralelo
CMD bash -c "\
  if [ -n \"$NGROK_AUTHTOKEN\" ]; then \
    ngrok config add-authtoken $NGROK_AUTHTOKEN; \
  fi && \
  /app/entrypoint.sh & \
  ngrok http ${PORT} --log=stdout"
