#!/usr/bin/env python3
"""
Desktop launcher for the certificate generator.

- Frozen Windows EXE: runs Streamlit in the background and shows a native window
  (no CMD). Closing the window stops the app.
- Source / Linux: same window if pywebview is available, otherwise the browser.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _exe_dir() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _app_root() -> Path:
    if _is_frozen():
        meipass = Path(getattr(sys, "_MEIPASS", _exe_dir()))
        for candidate in (meipass, _exe_dir() / "_internal", _exe_dir()):
            if (candidate / "certificate_ui.py").exists():
                return candidate
        return meipass
    return Path(__file__).resolve().parent


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_port(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.3)
    return False


def _show_error(message: str) -> None:
    print(message, file=sys.stderr)
    if _is_frozen() and os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "Générateur de certificats", 0x10)
            return
        except Exception:
            pass
    try:
        input("Appuyez sur Entrée pour quitter…")
    except Exception:
        pass


def _streamlit_argv(ui_script: Path, port: int) -> list[str]:
    return [
        "streamlit",
        "run",
        str(ui_script),
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
        "--server.fileWatcherType=none",
    ]


def _start_streamlit_thread(ui_script: Path, port: int) -> None:
    from streamlit.web import cli as stcli

    sys.argv = _streamlit_argv(ui_script, port)
    stcli.main()


def _start_streamlit_subprocess(ui_script: Path, port: int, cwd: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["CERT_APP_CHILD"] = "1"
    cmd = [sys.executable, "-m", *_streamlit_argv(ui_script, port)]
    return subprocess.Popen(cmd, cwd=str(cwd), env=env)


def _open_desktop_window(port: int) -> bool:
    """Open a native window. Returns False if pywebview is unavailable."""
    try:
        import webview
    except ImportError:
        return False

    url = f"http://127.0.0.1:{port}"
    webview.create_window(
        title="وزارة العدل — Générateur de certificats",
        url=url,
        width=1360,
        height=900,
        min_size=(960, 640),
    )
    webview.start()
    return True


def main() -> int:
    if os.environ.get("CERT_APP_CHILD") == "1" and _is_frozen():
        _show_error("Relance incorrecte de l'exécutable détectée.")
        return 1

    root = _app_root()
    workdir = _exe_dir()
    os.chdir(workdir)

    port = int(os.environ.get("CERT_APP_PORT", "8501"))
    ui_script = root / "certificate_ui.py"
    if not ui_script.exists():
        _show_error(f"Fichier introuvable:\n{ui_script}\n\nDossier app:\n{root}")
        return 1

    # Already running → focus via window/browser only.
    if _port_open(port):
        if not _open_desktop_window(port):
            webbrowser.open(f"http://127.0.0.1:{port}")
        return 0

    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    child: subprocess.Popen | None = None

    try:
        if _is_frozen():
            thread = threading.Thread(
                target=_start_streamlit_thread,
                args=(ui_script, port),
                daemon=True,
            )
            thread.start()
        else:
            child = _start_streamlit_subprocess(ui_script, port, root)

        if not _wait_for_port(port):
            _show_error(
                "Le serveur n'a pas démarré à temps.\n"
                "Vérifiez qu'aucun autre programme n'utilise le port 8501."
            )
            return 1

        # Prefer a real desktop window; fall back to the system browser.
        if not _open_desktop_window(port):
            print("====================================================")
            print("  وزارة العدل — Générateur de certificats")
            print(f"  http://127.0.0.1:{port}")
            print("  Fermez cette fenêtre pour arrêter l'application.")
            print("====================================================")
            webbrowser.open(f"http://127.0.0.1:{port}")
            if child is not None:
                return int(child.wait())
            # Frozen without pywebview: keep process alive with Streamlit thread.
            while True:
                time.sleep(1.0)

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        _show_error(f"Erreur au démarrage:\n{exc}")
        return 1
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except Exception:
                child.kill()


if __name__ == "__main__":
    raise SystemExit(main())
