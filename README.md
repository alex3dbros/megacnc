# Mega CNC

Software for controlling Megacell charger lithium cell testing devices.

---

## Architecture Overview

| Component | Technology |
|-----------|-----------|
| Web framework | Django 5.0 |
| Database | PostgreSQL (production) / SQLite (dev) |
| Task queue | Celery + Redis |
| Task scheduler | Celery Beat (django-celery-beat) |
| ASGI server | Daphne (optional, for WebSockets) |

The app polls Megacell charger hardware devices over HTTP every 5 seconds (via a Celery Beat periodic task), stores cell voltage/capacity/ESR data in the database, and serves a web dashboard on port 8000.

### UI (premium dark shell)

- **Theme:** Dark-only layout aligned with Deep Cycle Power branding (blue / lime accents). Global overrides live in `static/megacellcnc/css/megacnc-premium.css` (loaded from `dz.py`).
- **Dashboard:** Projects overview + **assign device to project** via dropdown (POST `assign-device-project/`). No need to delete/re-add devices.
- **Device / slots:** Operator-focused layout; slot charts use **Chart.js** with filled areas (voltage, current, temperature on one graph).
- **Cleanup:** Demo routes (shop, email demos, chart demos, etc.) were removed from `megacellcnc/urls.py`; unused template files may remain in `templates/` but are not linked.

### Docker (Linux / server)

For **PostgreSQL + Redis + Gunicorn + Celery worker + Celery Beat** (async tasks), see **[DOCKER.md](DOCKER.md)**.

---

## Quick Start — Windows / PyCharm (Development)

This is the **easiest** way to run the project locally for debugging. No PostgreSQL, no Redis, no Celery workers needed.

### Prerequisites

- **Python 3.11+** installed and on PATH
- **PyCharm** (Community or Professional)
- **Git**

### 1. Clone and open in PyCharm

```
git clone https://github.com/alex3dbros/megacnc.git
cd megacnc
```

Open the `megacnc` folder in PyCharm.

### 2. Create a virtual environment

In PyCharm: **File > Settings > Project > Python Interpreter > Add Interpreter > Add Local Interpreter > Virtualenv Environment > New**.

Or from the terminal:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** `psycopg2` may fail to build on Windows if you don't have PostgreSQL installed. If you only plan to use SQLite for development, you can ignore this error — the app will work fine with SQLite.

### 3. Configure environment (`.env` file)

Copy the example config:

```
copy .env.example .env
```

The default `.env` is already set up for **easy local development**:

```ini
DEBUG=True
DB_ENGINE=sqlite3        # Uses SQLite — no PostgreSQL needed
CELERY_EAGER=True        # Tasks run inline — no Redis/Celery needed
```

That's it. With these two settings, you can run the app from PyCharm without external services.

> **Important:** With `CELERY_EAGER=True` tasks execute synchronously when called, but the periodic device poller (Celery Beat) does NOT run. To poll devices, use the built-in management command — see step 7 below.

### 4. Run database migrations

```
python manage.py migrate
```

### 5. Create a superuser (optional, for Django admin)

```
python manage.py createsuperuser
```

### 6. Run the development server

```
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

### 7. Start the device poller (second terminal / run config)

The app needs to periodically poll your Megacell charger hardware for live data. In production this is done by Celery Beat, but for local dev there's a simple management command:

```
python manage.py poll_devices
```

This polls all registered devices every 5 seconds (same as Celery Beat would). Options:

```
python manage.py poll_devices --interval 10   # poll every 10 seconds
python manage.py poll_devices --once          # poll once and exit
```

### Desktop executable (Windows / Linux)

You can ship the app as a **PyInstaller onedir bundle** (executable + `_internal` + copied `templates/` / `static/`). Build **Windows on Windows** and **Linux on Linux** (or WSL).

- **Scripts:** `packaging/build_windows.ps1`, `packaging/build_linux.sh`
- **Details:** [`packaging/README.md`](packaging/README.md)
- **Runtime entry:** `packaging/launcher.py` (Waitress on port 8000, auto-migrate, background `poll_devices`, opens browser)

Quick try without building:

```
python packaging/launcher.py
```

### PyCharm Run Configurations

Create **two** run configurations:

**Config 1 — Django Server:**
1. **Run > Edit Configurations > + > Django Server**
2. Set Host: `127.0.0.1`, Port: `8000`
3. Environment variables: `DJANGO_SETTINGS_MODULE=dashboard.settings`
4. Working directory: path to the `megacnc` folder

**Config 2 — Device Poller:**
1. **Run > Edit Configurations > + > Python**
2. Script path: `manage.py`
3. Parameters: `poll_devices`
4. Working directory: path to the `megacnc` folder

Run both. You can **Debug** either one — breakpoints work in views, tasks, and the poller.

> With `CELERY_EAGER=True`, tasks triggered by the poller (like `check_device_status`) execute synchronously in the poller process, so breakpoints inside `tasks.py` will hit.

### Alternative: one-click batch script

Just double-click **`run_dev.bat`** — it creates the venv, installs deps, runs migrations, and starts the server. You still need to run `poll_devices` separately for live device data.

---

## Full Setup — Windows with PostgreSQL + Redis + Celery

Use this when you need the full production-like stack (e.g., to test periodic task scheduling, concurrent workers, etc.).

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+** — [download](https://www.postgresql.org/download/windows/)
- **Redis** — easiest option: [Memurai](https://www.memurai.com/) (Redis-compatible for Windows) or Redis via WSL/Docker

### 1. Set up PostgreSQL

1. Install PostgreSQL
2. Open **pgAdmin** or **psql** and create the database:

```sql
CREATE DATABASE mcccnc;
```

The default credentials in `.env.example` are:
- **User:** `postgres`
- **Password:** `MccAdmin`
- **Host:** `localhost`
- **Port:** `5432`

### 2. Set up Redis

**Option A — Memurai (native Windows):**

Download and install [Memurai](https://www.memurai.com/). It runs as a Windows service on port 6379.

**Option B — Docker:**

```
docker run -d -p 6379:6379 redis:alpine
```

**Option C — WSL:**

```
wsl --install
# Inside WSL:
sudo apt update && sudo apt install redis-server -y
sudo service redis-server start
```

### 3. Configure `.env`

```ini
DEBUG=True
DB_ENGINE=postgresql
DB_NAME=mcccnc
DB_USER=postgres
DB_PASSWORD=MccAdmin
DB_HOST=localhost
DB_PORT=5432
CELERY_EAGER=False
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Install dependencies and migrate

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

### 5. Start all services (4 terminals)

**Terminal 1 — Django dev server:**
```
python manage.py runserver
```

**Terminal 2 — Celery worker:**
```
celery -A dashboard worker --loglevel=info -P solo --concurrency=1
```

> `-P solo` is required on Windows (Celery's default prefork pool doesn't work on Windows).

**Terminal 3 — Celery Beat (periodic tasks):**
```
celery -A dashboard beat --loglevel=info
```

**Terminal 4 — Flower (optional, task monitoring UI):**
```
celery -A dashboard flower
```

Then open http://localhost:5555 for Flower.

---

## Deploying with Docker Compose (Ubuntu / Linux)

The canonical, up-to-date guide (services, env vars, migrations, troubleshooting) is **[DOCKER.md](DOCKER.md)**.

Quick reference:

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Install Docker Engine and Compose plugin on Ubuntu via your distro’s docs (e.g. `docker.io` / `docker-compose-plugin`). Tested on VirtualBox VMs and Raspberry Pi 4 (4GB RAM, 32GB SD card).

---

## Configuration Reference

All settings are controlled via the `.env` file in the project root. See `.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (insecure default) | Django secret key |
| `DEBUG` | `True` | Enable Django debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hosts |
| `DB_ENGINE` | `postgresql` | `postgresql` or `sqlite3` |
| `DB_NAME` | `mcccnc` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `MccAdmin` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `CELERY_EAGER` | `False` | `True` = tasks run inline (no Redis needed) |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis result backend URL |

---

## Project Structure

```
megacnc/
  dashboard/          Django project (settings, urls, celery, wsgi, asgi)
  megacellcnc/        Main app (models, views, tasks, forms, templates)
  mccprolib/          Local library for Megacell charger HTTP API
  static/             CSS, JS, images
  templates/          HTML templates
  .env                Local config (git-ignored)
  .env.example        Config template
  requirements.txt    Python dependencies
  docker-compose.yml  Production Docker setup
  DOCKER.md           Docker on Linux (full guide for clients / ops)
  run_dev.bat         One-click Windows dev startup
  manage.py           Django CLI
```

---

## Support and Donations

**Stripe:** https://buy.stripe.com/8wMdUmaZ00mc67m4gk

**PayPal:** https://www.paypal.com/donate/?hosted_button_id=B8Z5L9NE86KLC
