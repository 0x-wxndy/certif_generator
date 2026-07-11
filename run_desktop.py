#!/usr/bin/env python3
"""Desktop launcher: starts Streamlit and opens the browser."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        for candidate in (meipass, exe_dir / "_internal", exe_dir):
            if (candidate / "certificate_ui.py").exists():
                return candidate
        return meipass
    return Path(__file__).resolve().parent


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_and_open(port: int, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            webbrowser.open(f"http://localhost:{port}")
            return
        time.sleep(0.4)
    webbrowser.open(f"http://localhost:{port}")


def main() -> int:
    root = _app_root()
    os.chdir(root)
    port = int(os.environ.get("CERT_APP_PORT", "8501"))
    ui_script = root / "certificate_ui.py"
    if not ui_script.exists():
        print(f"[ERREUR] Fichier introuvable: {ui_script}")
        input("Appuyez sur Entrée pour quitter…")
        return 1

    # Prefer the bundled / venv python when not frozen.
    python = sys.executable
    cmd = [
        python,
        "-m",
        "streamlit",
        "run",
        str(ui_script),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        f"--server.port={port}",
        "--global.developmentMode=false",
    ]

    print("====================================================")
    print("  وزارة العدل — Générateur de certificats")
    print(f"  http://localhost:{port}")
    print("  Fermez cette fenêtre pour arrêter l'application.")
    print("====================================================")

    opener = threading.Thread(target=_wait_and_open, args=(port,), daemon=True)
    opener.start()

    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    try:
        process = subprocess.Popen(cmd, cwd=str(root), env=env)
        return process.wait()
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"[ERREUR] {exc}")
        input("Appuyez sur Entrée pour quitter…")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
