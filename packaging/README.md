# Mega CNC — desktop bundles (PyInstaller)

The web app can be shipped as a **folder** containing a native executable plus all DLLs/assets (**onedir**). This is more reliable for Django than a single `.exe` file.

## What you get

- **Windows:** `dist/MegaCNC/MegaCNC.exe` + `_internal/` + bundled `templates/`, `static/`, `.env.example`
- **Linux:** `dist/MegaCNC/MegaCNC` (same layout)

Runtime defaults (when running the frozen app) are set in `packaging/launcher.py`:

- `DB_ENGINE=sqlite3` — database file next to the executable (`db.sqlite3`)
- `CELERY_EAGER=True` — no Redis; Celery tasks run in-process
- Device polling uses a **background thread** running `poll_devices` (same as dev without Beat)

The server listens on **0.0.0.0:8000** (configurable with env vars `MEGACNC_HOST` / `MEGACNC_PORT`).  
**LAN access:** the frozen app sets `ALLOWED_HOSTS=*` by default (unless your `.env` already sets something else). If you still get “DisallowedHost”, edit the `.env` next to the exe and set `ALLOWED_HOSTS=*` or list your PC’s IP and hostnames.

## Build requirements

- **Build Windows on Windows**, **Linux on Linux** (or Linux VM / WSL for the Linux build). Cross-compiling with PyInstaller is not supported.
- Python 3.11+ recommended (match your dev version).
- Enough disk space: the bundle includes NumPy/Pandas and is typically **hundreds of MB**.

## Windows

```powershell
cd D:\path\to\megacnc
.\packaging\build_windows.ps1
```

First run creates `.venv-build` and installs dependencies.

Output: `dist\MegaCNC\` — zip that entire folder for distribution.

## Linux

```bash
cd /path/to/megacnc
chmod +x packaging/build_linux.sh
./packaging/build_linux.sh
```

Output: `dist/MegaCNC/` — tar.gz the whole directory.

## First run for end users

1. Unzip the folder.
2. Run `MegaCNC.exe` (Windows) or `./MegaCNC` (Linux).
3. If `.env` is missing, it is copied from `.env.example` next to the exe.
4. Browser should open to `http://127.0.0.1:8000/`.

## Optional environment (next to executable)

| Variable | Purpose |
|----------|---------|
| `MEGACNC_DATA_DIR` | Put `db.sqlite3` here instead of next to the exe (see `dashboard/settings.py`) |
| `MEGACNC_HOST` / `MEGACNC_PORT` | Bind address (default `0.0.0.0:8000`) |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Standard Django (via `.env`) |

## Development without building

```bash
pip install -r requirements.txt
python packaging/launcher.py
```

Same behaviour as the frozen app (migrations, poller thread, Waitress).

## `TemplateDoesNotExist` in the built `.exe`

Project HTML/CSS/JS are bundled under **`megacnc_dt_templates`** and **`megacnc_dt_static`** (not plain `templates`/`static`) so they are not overwritten by NumPy/Pandas data files. `dashboard/settings.py` searches those folder names next to the exe and under `_internal/`.

## NumPy / Pandas errors in the built `.exe`

If you see `No module named 'numpy._core._exceptions'` or `cannot load module more than once per process`, rebuild with the current `packaging/MegaCNC.spec` (it uses `collect_all('numpy')` and `collect_all('pandas')`). Older spec versions only listed `numpy` / `pandas` by name and missed NumPy 2.x internal modules.

## Troubleshooting

### `No module named 'celery.app.amqp'` (frozen `.exe`)

The bundle uses **`CELERY_EAGER=True`** (tasks run in-process), but **Celery + Kombu** must still be fully importable. PyInstaller often omits broker-related submodules until something calls `.delay()`.

**Fix:** rebuild with the current `packaging/MegaCNC.spec` (it runs `collect_submodules("celery")` and `collect_submodules("kombu")`). Do not strip `celery` from `requirements.txt` for the build venv.

### `Invalid requirement: 'D\x00j\x00a\x00n...'` (pip)

`requirements.txt` was saved as **UTF-16** (e.g. by some Windows editors). Pip expects **UTF-8**.

In VS Code / Cursor: bottom-right encoding -> **Save with Encoding** -> **UTF-8**.  
Or from PowerShell (repo root), rewrite as UTF-8:

```powershell
Get-Content -Path requirements.txt -Encoding Unicode | Set-Content -Path requirements.txt -Encoding utf8
```

(Back up the file first; this may add a blank line at the end.)

## Limitations

- **PostgreSQL / Redis / full Celery** are not targeted by the default bundle; use `.env` and a normal `manage.py runserver` deployment for that.
- **Code signing** on Windows and **AppImage/deb** packaging are not included (only raw PyInstaller output).
- Antivirus may flag PyInstaller executables briefly (false positives are common).
