#!/usr/bin/env python3
"""
Desktop launcher for the certificate generator.

Windows EXE (PyInstaller):
  Parent process  → native window (pywebview)
  Child process   → Streamlit server  (same .exe with --run-streamlit)

Closing the window stops the child server.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import traceback
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


def _log_path() -> Path:
    return _exe_dir() / "generateur_certificats.log"


def _log(message: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {message}"
    try:
        with open(_log_path(), "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_port(port: int, timeout: float = 120.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.4)
    return False


def _show_error(message: str) -> None:
    _log(f"ERROR: {message}")
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                message + f"\n\nLog: {_log_path()}",
                "Générateur de certificats",
                0x10,
            )
            return
        except Exception:
            pass
    try:
        input("Appuyez sur Entrée pour quitter…")
    except Exception:
        pass


def _streamlit_flag_options(port: int) -> dict:
    return {
        "server.headless": True,
        "server.address": "127.0.0.1",
        "server.port": port,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
        "server.fileWatcherType": "none",
    }


def _run_streamlit_server(ui_script: Path, port: int) -> int:
    """Blocking Streamlit server (used by the child process / source mode)."""
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    _log(f"Starting Streamlit on 127.0.0.1:{port}")
    _log(f"UI script: {ui_script}")

    # Prefer bootstrap API (more reliable under PyInstaller than rewriting sys.argv).
    try:
        from streamlit.web import bootstrap

        bootstrap.run(
            str(ui_script),
            is_hello=False,
            args=[],
            flag_options=_streamlit_flag_options(port),
        )
        return 0
    except TypeError:
        # Older/newer Streamlit signature differences.
        pass
    except Exception:
        _log("bootstrap.run failed:\n" + traceback.format_exc())

    try:
        from streamlit.web import cli as stcli

        sys.argv = [
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
        return int(stcli.main() or 0)
    except Exception:
        _log("stcli.main failed:\n" + traceback.format_exc())
        raise


def _open_desktop_window(port: int) -> bool:
    try:
        import webview
    except ImportError:
        _log("pywebview not installed — falling back to browser")
        return False

    url = f"http://127.0.0.1:{port}"
    _log(f"Opening desktop window: {url}")
    webview.create_window(
        title="وزارة العدل — Générateur de certificats",
        url=url,
        width=1360,
        height=900,
        min_size=(960, 640),
    )
    webview.start()
    return True


def _spawn_streamlit_child(ui_script: Path, port: int) -> subprocess.Popen:
    """
    Re-launch this EXE in server-only mode.
    Avoids running Streamlit in a fragile background thread.
    """
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["CERT_APP_CHILD"] = "1"

    if _is_frozen():
        cmd = [
            sys.executable,
            "--run-streamlit",
            str(port),
            str(ui_script),
        ]
    else:
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--run-streamlit",
            str(port),
            str(ui_script),
        ]

    _log("Spawning Streamlit child: " + " ".join(cmd))
    # Hide child console on Windows.
    creationflags = 0
    startupinfo = None
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    return subprocess.Popen(
        cmd,
        cwd=str(_exe_dir()),
        env=env,
        creationflags=creationflags,
        startupinfo=startupinfo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _drain_child_log(process: subprocess.Popen) -> None:
    """Copy child stdout into the log file (non-blocking-ish)."""
    if process.stdout is None:
        return
    try:
        for raw in iter(process.stdout.readline, b""):
            if not raw:
                break
            try:
                text = raw.decode("utf-8", errors="replace").rstrip()
            except Exception:
                text = str(raw)
            if text:
                _log("[streamlit] " + text)
    except Exception:
        _log("child log drain stopped:\n" + traceback.format_exc())


def main() -> int:
    # ----- Child mode: Streamlit server only -----
    if "--run-streamlit" in sys.argv:
        try:
            idx = sys.argv.index("--run-streamlit")
            port = int(sys.argv[idx + 1])
            ui_script = Path(sys.argv[idx + 2]).resolve()
        except Exception:
            root = _app_root()
            port = int(os.environ.get("CERT_APP_PORT", "8501"))
            ui_script = root / "certificate_ui.py"
        os.chdir(_exe_dir())
        try:
            return _run_streamlit_server(ui_script, port)
        except Exception as exc:
            _log("Child Streamlit crashed:\n" + traceback.format_exc())
            _show_error(f"Le serveur Streamlit a échoué:\n{exc}")
            return 1

    # ----- Parent mode: start server + show UI -----
    root = _app_root()
    workdir = _exe_dir()
    os.chdir(workdir)
    _log(f"Launcher start (frozen={_is_frozen()})")
    _log(f"exe_dir={workdir}")
    _log(f"app_root={root}")

    port = int(os.environ.get("CERT_APP_PORT", "8501"))
    ui_script = (root / "certificate_ui.py").resolve()
    if not ui_script.exists():
        _show_error(f"Fichier introuvable:\n{ui_script}\n\nDossier app:\n{root}")
        return 1

    child: subprocess.Popen | None = None

    try:
        if _port_open(port):
            _log(f"Port {port} already in use — reusing existing server")
        else:
            child = _spawn_streamlit_child(ui_script, port)
            import threading

            threading.Thread(target=_drain_child_log, args=(child,), daemon=True).start()

            if not _wait_for_port(port, timeout=120):
                extra = ""
                if child.poll() is not None:
                    extra = f"\nLe processus serveur s'est arrêté (code {child.returncode})."
                _show_error(
                    "Le serveur n'a pas démarré à temps."
                    f"{extra}\n\n"
                    "1) Fermez toute ancienne instance dans le Gestionnaire des tâches\n"
                    "2) Vérifiez le fichier generateur_certificats.log\n"
                    "3) Réessayez"
                )
                return 1
            _log("Server is up")

        if not _open_desktop_window(port):
            webbrowser.open(f"http://127.0.0.1:{port}")
            _log("Opened system browser (no pywebview)")
            if child is not None:
                return int(child.wait() or 0)
            _show_error(
                "pywebview est manquant.\n"
                "Réinstallez les dépendances puis reconstruisez l'EXE."
            )
            return 1

        _log("Window closed — shutting down")
        return 0
    except Exception as exc:
        _show_error(f"Erreur au démarrage:\n{exc}")
        return 1
    finally:
        if child is not None and child.poll() is None:
            _log("Terminating Streamlit child")
            child.terminate()
            try:
                child.wait(timeout=8)
            except Exception:
                child.kill()


if __name__ == "__main__":
    if os.name == "nt":
        try:
            from multiprocessing import freeze_support

            freeze_support()
        except Exception:
            pass
    raise SystemExit(main())
