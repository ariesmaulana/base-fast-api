from app.core.logger import AppLogger


def get_app_logger(path: str):
    """Dependency that provides an AppLogger instance."""
    return AppLogger(path)
