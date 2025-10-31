# 🧩 Tasklist — FastAPI + SQLAlchemy + Docker (+ Admin & Exports)

A multi-user task management application built with **FastAPI** and **SQLAlchemy**, featuring a secure **admin panel** at `/admin`, **JWT authentication** with configurable expiration, **bcrypt password hashing**, and **task export** to **XLSX/CSV**.
It also includes a minimal HTML UI for login, registration, and task browsing.

---

## 📘 Overview

- Each user has their **own account** and **private task list**.
- Through **mention tags** (`@username`), users can **create shared tasks** — the system automatically replicates the task for the mentioned users (using the *handle*, i.e., the part before `@` in their email).
- Allows **creating**, **deleting**, and **updating** task status (`pending` ↔ `done`).
- `/admin` provides a **secure administration dashboard** (via SQLAdmin) using real credentials; authorized users are defined in `.env` (`ADMIN_EMAILS`).
- Supports **task export** in **XLSX** and **CSV** formats, keeping filters and sorting.
- Passwords are stored using **bcrypt**, and JWT tokens have a **configurable expiration** (default: 60 min) set via `.env`.

---

## ✨ Key Features

- 🔐 **JWT authentication** with HttpOnly cookies
- 👥 **Shared tasks** through `@handle` mentions
- 📤 **Task export** to Excel and CSV
- 🧱 **Secure admin panel** at `/admin` (whitelisted users)
- ⚙️ **Environment-based configuration** (`.env`)
- 📜 **Auto-generated API documentation** (`/docs`, `/redoc`)
- 🧪 **Test suite** covering users, tasks, mentions, and admin access

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file at the project root:

```env
# --- Database ---
# PostgreSQL (recommended for Docker):
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/tasklist

# --- App / JWT ---
SECRET_KEY=super_secret_key_change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# --- CORS (optional) ---
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# --- Admin whitelist ---
ADMIN_EMAILS=admin@yourdomain.com
```

---

## 🐳 Run with Docker (Recommended)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/tasklist.git
cd tasklist
```

### 2️⃣ Create your `.env` file

Follow the example above.

### 3️⃣ Build and run the containers

```bash
docker compose up --build
```

This will automatically start:

- `web`: FastAPI backend
- `db`: PostgreSQL database

### 4️⃣ Access the app

| URL                             | Description            |
| ------------------------------- | ---------------------- |
| `http://localhost:8000`       | API root               |
| `http://localhost:8000/docs`  | Swagger UI             |
| `http://localhost:8000/redoc` | ReDoc UI               |
| `http://localhost:8000/app`   | Minimal HTML interface |
| `http://localhost:8000/admin` | Admin dashboard        |

> 💡 Want to share it online? Use **Ngrok**:
>
> ```bash
> ngrok http 8000
> ```

---

## 👤 Users, Tasks, and Mentions

### Register & Login

- `POST /auth/register` → create a user
- `POST /auth/login` → obtain an access token

### Tasks

- `POST /tasks` → create a task (requires token or cookie)
- `GET /tasks` → list tasks with pagination
- `PUT /tasks/{id}` → update task text or status
- `DELETE /tasks/{id}` → delete a task

### Mentions

If the `text` field includes `@username`, the task will be automatically replicated for the user whose email prefix matches that handle.

📘 **Example: creating a shared task**

```bash
curl -X POST http://localhost:8000/tasks   -H "Authorization: Bearer <TOKEN>"   -H "Content-Type: application/json"   -d '{"text":"Review PR with @maria #backend", "status":"pending"}'
```

---

## 🧠 Admin Panel

- Accessible at `/admin`
- Uses real user credentials (email + password)
- Access restricted via the `ADMIN_EMAILS` whitelist in `.env`
- **Fail-closed**: if no admin emails are set, nobody can log in
- Predefined views for `User` and `Task` (list, search, sort)

---

## 📤 Export Features

- **Excel (XLSX)** → `GET /tasks-export.xlsx`
- **CSV** → `GET /tasks-export.csv`

Both endpoints support filters and sorting (`status`, `q`, `sort`, `dir`).

---

## 🛡️ Security

- Passwords hashed with **bcrypt**
- JWT with:
  - Configurable algorithm (`ALGORITHM`, default `HS256`)
  - Configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Tokens can be sent via:
  - `Authorization: Bearer <token>` header
  - HttpOnly cookie (used in HTML UI)

---

## 🧪 Tests

The project includes a **Pytest** test suite covering:

1. **User registration and login**
2. **Task CRUD** (create, update, delete)
3. **Task sharing via `@handle` mentions**
4. **Auth-required routes and permissions**
5. **Admin panel access control**
6. **CSV/XLSX export integrity**

Run all tests locally with:

```bash
pytest -q
```

---

## 📚 API Documentation

The API is self-documented via FastAPI’s OpenAPI integration:

- **Swagger UI** → [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** → [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Raw JSON schema** → [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🪪 License

This project is released under **The Unlicense** — Public Domain.
You are free to use, copy, modify, publish, compile, sell, or distribute this software, with or without changes, for any purpose.
