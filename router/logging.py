import logging.config
import logging.handlers
import os
import re
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Custom TimedRotatingFileHandler that creates date-based filenames."""

    def __init__(self, filename: str, **kwargs: Any) -> None:
        """Initialize with a base filename pattern."""
        self.base_dir = os.path.dirname(filename)
        self.base_name = os.path.basename(filename).replace(".log", "")

        today = datetime.now().strftime("%Y-%m-%d")
        self.current_date = today
        dated_filename = os.path.join(self.base_dir, f"{self.base_name}_{today}.log")

        super().__init__(dated_filename, **kwargs)

    def doRollover(self) -> None:
        """Override rollover to create new date-based filename."""
        if self.stream:
            self.stream.close()

        new_date = datetime.now().strftime("%Y-%m-%d")
        new_filename = os.path.join(self.base_dir, f"{self.base_name}_{new_date}.log")

        self.baseFilename = new_filename
        self.current_date = new_date

        # FIX ME: not sure if we need this
        # self._cleanup_old_files()

        if not self.delay:
            self.stream = self._open()

    def _cleanup_old_files(self) -> None:
        """Remove old log files beyond backupCount."""
        if self.backupCount > 0:
            log_files = []
            if os.path.exists(self.base_dir):
                for file in os.listdir(self.base_dir):
                    if file.startswith(f"{self.base_name}_") and file.endswith(".log"):
                        file_path = os.path.join(self.base_dir, file)
                        log_files.append((file_path, os.path.getmtime(file_path)))

            log_files.sort(key=lambda x: x[1], reverse=True)

            for file_path, _ in log_files[self.backupCount :]:
                try:
                    os.remove(file_path)
                except OSError:
                    pass


def get_package_version() -> str:
    """Read the package version from pyproject.toml."""
    try:
        # Find project root by looking for pyproject.toml
        current_path = Path(__file__).parent
        while current_path != current_path.parent:
            pyproject_path = current_path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                version = pyproject_data.get("project", {}).get("version", "unknown")
                return version
            current_path = current_path.parent

        # Fallback: try the simple path resolution (3 levels up for router/logging/logging_config.py)
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
            version = pyproject_data.get("project", {}).get("version", "unknown")
            return version

        return "unknown"
    except Exception:
        return "unknown"


class VersionFilter(logging.Filter):
    """Filter to add package version to all log records."""

    def __init__(self) -> None:
        super().__init__()
        self.version = get_package_version()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add version information to the log record."""
        record.version = self.version
        return True


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs."""

    SENSITIVE_KEYS = {
        "authorization",
        "x-cashu",
        "bearer",
        "token",
        "key",
        "secret",
        "password",
        "cashu_token",
        "bearer_key",
        "api_key",
        "nsec",
        "upstream_api_key",
        "refund_address",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out sensitive information from log records."""
        try:
            message = record.getMessage()

            for key in self.SENSITIVE_KEYS:
                if key in message.lower():
                    patterns = [
                        rf"{key}[:\s=]+([a-zA-Z0-9_\-\.]+)",  # key: value or key=value
                        rf'{key}[:\s=]+["\']([^"\']+)["\']',  # key: "value" or key='value'
                        r"Bearer\s+([a-zA-Z0-9_\-\.]+)",  # Bearer token
                        r"cashu[A-Z]+([a-zA-Z0-9_\-\.=/+]+)",  # Cashu tokens
                    ]

                    for pattern in patterns:
                        message = re.sub(
                            pattern, f"{key}: [REDACTED]", message, flags=re.IGNORECASE
                        )

            record.msg = message
            record.args = ()

        except Exception:
            pass

        return True


def get_log_level() -> str:
    """Get log level from environment variable."""
    return os.environ.get("LOG_LEVEL", "INFO").upper()


def should_enable_console_logging() -> bool:
    """Check if console logging should be enabled."""
    return os.environ.get("ENABLE_CONSOLE_LOGGING", "true").lower() in (
        "true",
        "1",
        "yes",
    )


def setup_logging() -> None:
    """Configure centralized logging for the application."""

    log_level = get_log_level()
    console_enabled = should_enable_console_logging()

    # Determine which handlers to use
    handlers = ["file"]
    if console_enabled:
        handlers.append("console")

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(version)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s v%(version)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "filters": {
            "version_filter": {"()": VersionFilter},
            "security_filter": {"()": SecurityFilter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
                "filters": ["version_filter", "security_filter"],
            },
            "file": {
                "()": DailyRotatingFileHandler,
                "level": log_level,
                "formatter": "json",
                "filename": "logs/app.log",
                "when": "midnight",  # Rotate at midnight each day
                "interval": 1,  # Every 1 day
                "backupCount": 30,  # Keep 30 days of logs
                "atTime": None,  # Rotate at midnight (00:00)
                "filters": ["version_filter", "security_filter"],
            },
        },
        "loggers": {
            "router": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            "router.payment": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            "router.cashu": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            "router.proxy": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            "router.auth": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            # Suppress verbose third-party logging
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"] if console_enabled else [],
                "propagate": False,
            },
            "httpcore": {
                "level": "WARNING",
                "handlers": ["console"] if console_enabled else [],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["console"] if console_enabled else [],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"] if console_enabled else [],
        },
    }

    os.makedirs("logs", exist_ok=True)

    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name."""
    return logging.getLogger(name)
