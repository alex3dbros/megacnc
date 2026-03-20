# Mega CNC — Docker on Linux

Guide for running the full stack: **PostgreSQL**, **Redis**, **Gunicorn**, **Celery worker**, and **Celery Beat** (async tasks via Redis) on **Linux** (bare metal, VM, or cloud).

> **Note:** `docker-compose.yml` uses `network_mode: host`. This mode targets **Linux**; on Docker Desktop (Windows/macOS) behaviour may differ. For production, a **Linux server** is the supported setup described here.

---

## Requirements

- **Docker** and **Docker Compose** v2 (`docker compose`)
- **Linux** x86_64 or ARM64 (recommended)
- Host ports available: **5432** (PostgreSQL), **6379** (Redis), **8000** (web app)

---

## What `docker-compose.yml` starts

| Service         | Role |
|-----------------|------|
| `db`            | PostgreSQL, database `mcccnc` |
| `redis`         | Celery broker + result backend |
| `web`           | Gunicorn — `http://0.0.0.0:8000` |
| `celeryworker`  | Celery workers (e.g. device config, commands) |
| `celerybeat`    | Periodic scheduler (e.g. device polling ~every 5s) + `django_celery_beat` |

Environment variables for `web`, `celeryworker`, and `celerybeat` are set in Compose so that:

- `DB_ENGINE=postgresql` and `DB_HOST=localhost` (with **host** networking, services reach Postgres/Redis on the host)
- `CELERY_EAGER=False` — tasks run **asynchronously** through Redis (not inside the Django process)
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` = `redis://localhost:6379/0`

`dashboard/settings.py` reads **`DB_NAME`**, **`DB_USER`**, **`DB_PASSWORD`**, **`DB_HOST`**, **`DB_PORT`** — it does **not** parse a `DATABASE_URL` string from Docker env.

---

## Quick start

From the repository root:

```bash
cd /path/to/megacnc

# Build images and start in the background
docker compose up --build -d
```

Check containers:

```bash
docker compose ps
```

Logs (optional):

```bash
docker compose logs -f web celeryworker celerybeat
```

Web UI: **`http://<server-ip>:8000/`** (or `http://127.0.0.1:8000/` locally).

---

## Migrations and admin user

The `web` container name may look like `megacnc-web-1` (depends on the project folder name). Run:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Stop and cleanup

```bash
docker compose down
```

PostgreSQL data persists in the Docker volume **`postgres_data`** (defined in Compose). `docker compose down -v` also removes volumes (**warning:** you will lose the database).

---

## `.env` file (optional; recommended for production)

Copy `.env.example` to `.env` and adjust values. For Docker, do **not** leave `CELERY_EAGER=True` if you want real workers (Compose sets `CELERY_EAGER=False` explicitly on the app services).

Useful variables:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Required in production (change the default) |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames or IPs |

To load secrets from a file, add `env_file: .env` under each Django/Celery service in `docker-compose.yml`. Values in the `environment:` section override `.env` where both define the same key.

---

## Desktop bundle (PyInstaller) vs Docker

| Mode | Database | Celery |
|------|----------|--------|
| **Desktop** (`packaging/launcher.py`) | SQLite by default | `CELERY_EAGER=True` — no separate Redis worker |
| **Docker (this guide)** | PostgreSQL | Redis + worker + beat — async tasks |

See `packaging/README.md` for the Windows `.exe` bundle.

---

## Troubleshooting

### Web service fails / migration errors

- Wait a few seconds after `up` for PostgreSQL to accept connections, then run `migrate` again.
- Ensure port **5432** is not used by another Postgres instance on the host.

### Celery tasks do not run

- Check `docker compose logs celeryworker` and `redis`.
- Confirm `CELERY_EAGER=False` in the container (`docker compose exec web env | grep CELERY`).

### `network_mode: host` on Windows

This Compose file is intended for **Linux**. On Windows, use WSL2 with Docker, or run the stack on a Linux server.

---

## systemd (start on boot)

See `Creating a service.txt` for an example — adjust the path to `docker-compose.yml` and use the `docker compose` (or `docker-compose`) command available on your system.
