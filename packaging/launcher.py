#!/usr/bin/env python3
"""
Mega CNC desktop entry point.

- Development:  python packaging/launcher.py
- PyInstaller:  executable sets MEGACNC_BUNDLE_ROOT to the folder that contains
  templates/, static/, .env — typically the same directory as the .exe (onedir).

Starts Waitress (HTTP), runs migrations, opens the browser, and spawns a
background device poller thread (replaces Celery Beat when CELERY_EAGER=True).
"""
from __future__ import annotations

import os
import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def bundle_root() -> Path:
    """Directory with templates/, static/, .env (writable)."""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    # Repo root (parent of packaging/)
    return Path(__file__).resolve().parent.parent


def _ensure_env_file(root: Path) -> None:
    env_path = root / ".env"
    example = root / ".env.example"
    if not env_path.exists() and example.exists():
        shutil.copy(example, env_path)


def _apply_bundle_defaults() -> None:
    """Safe defaults when running from a built bundle (override only if unset)."""
    if not _is_frozen():
        return
    os.environ.setdefault("DB_ENGINE", "sqlite3")
    os.environ.setdefault("CELERY_EAGER", "True")
    os.environ.setdefault("DEBUG", "True")
    # Allow access from LAN (bind is 0.0.0.0). Tighten in .env e.g. ALLOWED_HOSTS=192.168.1.10,localhost
    os.environ.setdefault("ALLOWED_HOSTS", "*")


def _start_poller_daemon() -> None:
    from django.core.management import call_command

    def _run() -> None:
        try:
            call_command("poll_devices", verbosity=1)
        except Exception as exc:  # pragma: no cover
            print(f"[MegaCNC] Poller stopped: {exc}", file=sys.stderr)

    t = threading.Thread(target=_run, name="megacnc-poll_devices", daemon=True)
    t.start()


def main() -> int:
    root = bundle_root()
    os.environ["MEGACNC_BUNDLE_ROOT"] = str(root)
    os.chdir(root)

    # Running `python packaging/launcher.py` puts `packaging/` on sys.path, not the repo root — Django
    # needs the project root for `dashboard`, `dz`, `custom_context_processor`. Frozen exe uses PyInstaller's path.
    if not _is_frozen():
        root_str = str(root.resolve())
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    _ensure_env_file(root)
    _apply_bundle_defaults()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard.settings")

    import django

    django.setup()

    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=1)

    _start_poller_daemon()

    def _open_browser() -> None:
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000/")

    threading.Thread(target=_open_browser, daemon=True).start()

    host = os.getenv("MEGACNC_HOST", "0.0.0.0")
    port = int(os.getenv("MEGACNC_PORT", "8000"))

    print(f"[MegaCNC] Local:   http://127.0.0.1:{port}/")
    print(f"[MegaCNC] Network: http://<this-pc-ip>:{port}/  (listening on {host}:{port})")
    print("[MegaCNC] Close this window to stop the server.")

    try:
        from waitress import serve
        from dashboard.wsgi import application

        serve(application, listen=f"{host}:{port}", threads=6)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
