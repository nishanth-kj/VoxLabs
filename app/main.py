"""VoxLabs desktop entry point: `uv run python -m app.main`.

`--self-test` starts the app, builds every page, imports every engine in the build and quits with
exit code 0. The build script runs the finished bundle with it, so a bundle that is missing a module,
or an engine that breaks without a console, fails the build.

A built (windowed) app has no console, so a crash at startup is written to a crash report:
VOXLABS_CRASH_REPORT, or VoxLabs-crash.txt in the temp folder.
"""

import os
import sys


def _ensure_std_streams() -> None:
    """A windowed build has no console, so sys.stdout/stderr are None. Libraries that print or add a log
    sink crash then (Kokoro logs to sys.stderr as soon as it is imported, download progress bars write
    to it): give them a sink that discards the output. Our own logs still go to the file and the panel."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _import_bundled_engines() -> None:
    """Self-test: import every engine library this build contains, which runs its setup code."""
    import importlib

    from app.constants.models import MODEL_CATALOG
    from app.utils.model import package_installed

    for entry in MODEL_CATALOG:
        package = entry.get("package")
        if package and package_installed(package):
            importlib.import_module(package)


def _use_own_taskbar_icon() -> None:
    """Group VoxLabs under its own taskbar entry and icon instead of python.exe's."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VoxLabs.Desktop")
    except Exception:  # cosmetic only; never block startup
        pass


def main() -> int:
    _ensure_std_streams()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from app.services.job_service import job_service
    from app.services.model_service import model_service
    from app.services.system_service import VERSION, system_service
    from app.utils.logger import enable_file_logging, logger, set_log_source

    set_log_source("ui")  # this thread is the Qt UI thread
    system_service.initialize()
    enable_file_logging()
    logger.info(f"Starting VoxLabs desktop {VERSION}")

    if sys.platform == "win32":
        _use_own_taskbar_icon()
    app = QApplication(sys.argv)
    app.setApplicationName("VoxLabs")
    app.setOrganizationName("VoxLabs")

    from app.ui import icons

    app.setWindowIcon(icons.app_icon())  # every window, dialog and message box inherits it

    from app.ui.theme import apply_theme

    apply_theme(app, system_service.get_setting("theme"))

    from app.ui.main_window import MainWindow
    from app.ui.widgets.progress import show_error

    window = MainWindow()
    window.show()

    self_test = "--self-test" in sys.argv
    if self_test:
        _import_bundled_engines()  # raises (and fails the self-test) if an engine cannot load here
        QTimer.singleShot(0, app.quit)  # every page is built: the bundle works
    elif system_service.get_setting("api_enabled"):
        try:
            system_service.start_api()
        except Exception as exc:  # the desktop app works without the API
            show_error(window, exc, "REST API not started")

    code = app.exec()
    logger.info("Shutting down")
    system_service.stop_api()
    job_service.shutdown(wait=False)
    model_service.unload_all()
    if self_test:
        print(f"VoxLabs {VERSION} self-test OK")
    return code


def _report_crash(exc: BaseException) -> None:
    import tempfile
    import traceback

    path = os.environ.get("VOXLABS_CRASH_REPORT") or os.path.join(tempfile.gettempdir(), "VoxLabs-crash.txt")
    try:
        with open(path, "w", encoding="utf-8") as report:
            report.write("".join(traceback.format_exception(exc)))
    except OSError:
        pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _report_crash(exc)
        if "--self-test" in sys.argv:
            sys.exit(1)  # A windowed PyInstaller error dialog would block unattended builds.
        raise
