#!/usr/bin/env python3
"""Desktop launcher: starts Streamlit and opens the browser once."""

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
    """Folder that contains certificate_ui.py and bundled assets."""
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


def _wait_and_open(port: int, timeout: float = 60.0) -> None:
    """Open the browser a single time once the server accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            webbrowser.open(f"http://127.0.0.1:{port}")
            return
        time.sleep(0.35)
    # Last attempt even if health-check timed out.
    webbrowser.open(f"http://127.0.0.1:{port}")


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


def _run_streamlit_inprocess(ui_script: Path, port: int) -> int:
    """Run Streamlit inside this process (required for PyInstaller EXE)."""
    from streamlit.web import cli as stcli

    sys.argv = _streamlit_argv(ui_script, port)
    return int(stcli.main() or 0)


def _run_streamlit_subprocess(ui_script: Path, port: int, cwd: Path) -> int:
    """Dev / source mode: spawn `python -m streamlit`."""
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [sys.executable, "-m", *_streamlit_argv(ui_script, port)]
    process = subprocess.Popen(cmd, cwd=str(cwd), env=env)
    return int(process.wait())


def main() -> int:
    # Guard: never re-exec the frozen EXE as if it were Python.
    if os.environ.get("CERT_APP_CHILD") == "1" and _is_frozen():
        print("[ERREUR] Relance incorrecte de l'exécutable détectée.")
        return 1

    root = _app_root()
    workdir = _exe_dir()  # writable location next to the .exe
    os.chdir(workdir)

    port = int(os.environ.get("CERT_APP_PORT", "8501"))
    ui_script = root / "certificate_ui.py"
    if not ui_script.exists():
        print(f"[ERREUR] Fichier introuvable: {ui_script}")
        print(f"         Dossier app : {root}")
        input("Appuyez sur Entrée pour quitter…")
        return 1

    # Already running → just open the browser, don't spawn another server.
    if _port_open(port):
        print(f"L'application tourne déjà sur http://127.0.0.1:{port}")
        webbrowser.open(f"http://127.0.0.1:{port}")
        return 0

    print("====================================================")
    print("  وزارة العدل — Générateur de certificats")
    print(f"  http://127.0.0.1:{port}")
    print("  Fermez cette fenêtre pour arrêter l'application.")
    print("====================================================")
    print()

    opener = threading.Thread(target=_wait_and_open, args=(port,), daemon=True)
    opener.start()

    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["CERT_APP_CHILD"] = "1"

    try:
        if _is_frozen():
            return _run_streamlit_inprocess(ui_script, port)
        return _run_streamlit_subprocess(ui_script, port, root)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"[ERREUR] {exc}")
        import traceback

        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter…")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
