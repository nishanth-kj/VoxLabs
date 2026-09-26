"""VoxLabs desktop entry point: `uv run python -m app.main`."""

import sys


def _use_own_taskbar_icon() -> None:
    """Group VoxLabs under its own taskbar entry and icon instead of python.exe's."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VoxLabs.Desktop")
    except Exception:  # cosmetic only; never block startup
        pass


def main() -> int:
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

    if system_service.get_setting("api_enabled"):
        try:
            system_service.start_api()
        except Exception as exc:  # the desktop app works without the API
            show_error(window, exc, "REST API not started")

    code = app.exec()
    logger.info("Shutting down")
    system_service.stop_api()
    job_service.shutdown(wait=False)
    model_service.unload_all()
    return code


if __name__ == "__main__":
    sys.exit(main())
