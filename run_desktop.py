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


def _apply_streamlit_env(port: int) -> None:
    """Force Streamlit settings via env (read before config parse)."""
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    # Required for embedding inside pywebview (otherwise blank / Not Found).
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"


def _streamlit_flag_options(port: int) -> dict:
    # Underscore form is converted to dotted config keys by load_config_options.
    return {
        "server_port": port,
        "server_address": "127.0.0.1",
        "server_headless": True,
        "browser_gatherUsageStats": False,
        "global_developmentMode": False,
        "server_fileWatcherType": "none",
        "server_enableXsrfProtection": False,
        "server_enableCORS": False,
    }


def _http_app_ready(port: int) -> bool:
    """True when Streamlit serves a real page (not plain 'Not Found')."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1.5) as resp:
            body = resp.read(4096).decode("utf-8", errors="ignore")
            if resp.status != 200:
                return False
            low = body.lower()
            if "not found" == body.strip().lower():
                return False
            return ("streamlit" in low) or ("<!doctype html" in low) or ("<html" in low)
    except Exception:
        return False


def _wait_for_app(port: int, timeout: float = 120.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _http_app_ready(port):
            return True
        time.sleep(0.5)
    return False


def _run_streamlit_server(ui_script: Path, port: int) -> int:
    """Blocking Streamlit server (used by the child process / source mode)."""
    _apply_streamlit_env(port)
    _log(f"Starting Streamlit on 127.0.0.1:{port}")
    _log(f"UI script: {ui_script}")

    flag_options = _streamlit_flag_options(port)

    # Prefer bootstrap API, but MUST call load_config_options first (cli does this).
    try:
        from streamlit.web import bootstrap

        bootstrap.load_config_options(flag_options=flag_options)
        bootstrap.run(
            str(ui_script),
            is_hello=False,
            args=[],
            flag_options=flag_options,
        )
        return 0
    except TypeError:
        pass
    except Exception:
        _log("bootstrap.run failed:\n" + traceback.format_exc())

    try:
        from streamlit.web import cli as stcli

        sys.argv = [
            "streamlit",
            "run",
            str(ui_script),
            f"--server.port={port}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--global.developmentMode=false",
            "--server.fileWatcherType=none",
            "--server.enableXsrfProtection=false",
            "--server.enableCORS=false",
        ]
        return int(stcli.main() or 0)
    except Exception:
        _log("stcli.main failed:\n" + traceback.format_exc())
        raise


def _unblock_packaged_dlls() -> None:
    """
    Clear Windows Mark-of-the-Web (Zone.Identifier) on bundled DLLs.

    Copied/zipped EXEs often fail to load pythonnet's Python.Runtime.dll with:
    "Failed to resolve Python.Runtime.Loader.Initialize".
    """
    if os.name != "nt" or not _is_frozen():
        return

    roots = {
        _exe_dir(),
        Path(getattr(sys, "_MEIPASS", _exe_dir())),
        _exe_dir() / "_internal",
    }
    for root in roots:
        if not root.exists():
            continue
        try:
            # Fast path: unblock the whole package tree once.
            _run = subprocess.run
            _run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    f'Get-ChildItem -LiteralPath "{root}" -Recurse -Include *.dll,*.exe '
                    f"-ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue",
                ],
                capture_output=True,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            _log(f"Unblock-File skipped for {root}: {exc}")


def _prepare_pythonnet_runtime() -> None:
    """Prefer .NET Core for pythonnet when available (more reliable when frozen)."""
    if os.name != "nt":
        return
    try:
        from pythonnet import set_runtime
        from clr_loader import get_coreclr

        set_runtime(get_coreclr())
        _log("pythonnet runtime: coreclr")
    except Exception as exc:
        _log(f"pythonnet coreclr unavailable, using default: {exc}")


def _show_info(message: str) -> None:
    _log(message.replace("\n", " | "))
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                "Générateur de certificats",
                0x40,
            )
            return
        except Exception:
            pass
    try:
        input(message + "\nAppuyez sur Entrée…")
    except Exception:
        pass


def _ui_mode() -> str:
    """
    browser = Edge/Chrome (default — works on virtually any Windows PC)
    native  = pywebview window (needs WebView2 + unblocked DLLs)
    """
    explicit = os.environ.get("CERT_UI_MODE", "").strip().lower()
    if explicit in {"browser", "native", "auto"}:
        return explicit
    if (_exe_dir() / "fenetre_native.on").exists():
        return "native"
    # Default: browser — white native windows are too common across PCs.
    return "browser"


def _webview2_installed() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg
    except ImportError:
        return False

    keys = (
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    )
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for key in keys:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    version, _ = winreg.QueryValueEx(handle, "pv")
                    if version and version != "0.0.0.0":
                        return True
            except OSError:
                continue
    # Edge often bundles WebView2.
    edge = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application"
    return edge.exists()


def _open_in_browser(port: int) -> None:
    url = f"http://127.0.0.1:{port}/"
    # Prefer Edge if present (closest to WebView2), else default browser.
    if os.name == "nt":
        edge = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
        if not edge.exists():
            edge = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
        if edge.exists():
            try:
                subprocess.Popen(
                    [str(edge), f"--new-window", url],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                _log(f"Opened Edge: {url}")
                return
            except Exception as exc:
                _log(f"Edge launch failed: {exc}")
    webbrowser.open(url)
    _log(f"Opened system browser: {url}")


def _run_browser_ui(port: int, child: subprocess.Popen | None) -> int:
    """Most compatible UI path for Windows deployments."""
    # Extra beat so Streamlit websocket/session is fully up before the browser hits it.
    time.sleep(1.2)
    _open_in_browser(port)
    _show_info(
        "L'application est ouverte dans votre navigateur.\n\n"
        f"Adresse: http://127.0.0.1:{port}/\n\n"
        "Travaillez dans le navigateur.\n"
        "Cliquez sur OK ici pour FERMER l'application."
    )
    _log("Browser UI session ended by user")
    return 0


def _open_desktop_window(port: int) -> bool:
    if not _webview2_installed():
        _log("WebView2 Runtime introuvable — native window skipped")
        return False

    _unblock_packaged_dlls()
    _prepare_pythonnet_runtime()

    try:
        import webview
    except ImportError:
        _log("pywebview not installed - falling back to browser")
        return False

    url = f"http://127.0.0.1:{port}/"
    storage = _exe_dir() / ".webview_data"
    storage.mkdir(parents=True, exist_ok=True)
    _log(f"Opening desktop window: {url}")

    try:
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.create_window(
            title="وزارة العدل — Générateur de certificats",
            url=url,
            width=1360,
            height=900,
            min_size=(960, 640),
        )

        # Give Streamlit a moment after HTTP-ready before the WebView paints.
        time.sleep(1.0)
        try:
            webview.start(storage_path=str(storage), private_mode=False)
        except TypeError:
            webview.start()
        return True
    except Exception:
        _log("pywebview failed:\n" + traceback.format_exc())
        return False


def _spawn_streamlit_child(ui_script: Path, port: int) -> subprocess.Popen:
    """
    Re-launch this EXE in server-only mode.
    Avoids running Streamlit in a fragile background thread.
    """
    env = os.environ.copy()
    env["CERT_APP_CHILD"] = "1"
    env["CERT_DESKTOP"] = "1"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    env["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    env["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

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
        if _port_open(port) and _http_app_ready(port):
            _log(f"Port {port} already serving Streamlit — reusing")
        else:
            if _port_open(port) and not _http_app_ready(port):
                _log(
                    f"Port {port} is occupied but not serving Streamlit. "
                    "Close old GenerateurCertificats processes, then retry."
                )
                _show_error(
                    f"Le port {port} est déjà utilisé par un ancien processus.\n"
                    "Fermez GenerateurCertificats dans le Gestionnaire des tâches,\n"
                    "puis relancez l'application."
                )
                return 1

            child = _spawn_streamlit_child(ui_script, port)
            import threading

            threading.Thread(target=_drain_child_log, args=(child,), daemon=True).start()

            # Wait until Streamlit returns a real HTML page (port open alone is not enough).
            if not _wait_for_app(port, timeout=120):
                extra = ""
                if child.poll() is not None:
                    extra = f"\nLe processus serveur s'est arrêté (code {child.returncode})."
                _show_error(
                    "L'interface n'a pas démarré correctement."
                    f"{extra}\n\n"
                    "1) Fermez toute ancienne instance dans le Gestionnaire des tâches\n"
                    "2) Vérifiez generateur_certificats.log\n"
                    "3) Reconstruisez l'EXE avec build_exe.bat"
                )
                return 1
            _log("Streamlit app is ready")

        mode = _ui_mode()
        _log(f"UI mode: {mode}")

        use_native = mode == "native" or (
            mode == "auto" and _webview2_installed()
        )
        if use_native:
            opened = False
            try:
                opened = _open_desktop_window(port)
            except Exception:
                _log("desktop window raised:\n" + traceback.format_exc())
                opened = False
            if opened:
                _log("Window closed — shutting down")
                return 0
            _log("Native window unavailable — falling back to browser")

        # Default / fallback: system browser (most reliable on any Windows PC).
        return _run_browser_ui(port, child)
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
