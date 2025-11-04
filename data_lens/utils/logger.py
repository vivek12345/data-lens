"""
Reusable logging configuration for the application.

Usage:
    from app.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# ANSI color codes for colored console output
class LogColors:
    """ANSI color codes for terminal output."""

    GREY = "\033[90m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD_RED = "\033[1;91m"
    RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color-coded log levels."""

    LEVEL_COLORS = {
        logging.DEBUG: LogColors.GREY,
        logging.INFO: LogColors.BLUE,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BOLD_RED,
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: bool = True,
    ):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors and sys.stderr.isatty():
            # Add color to the levelname
            levelname = record.levelname
            color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
            record.levelname = f"{color}{levelname}{LogColors.RESET}"

            # Format the message
            formatted = super().format(record)

            # Reset levelname to original (to avoid side effects)
            record.levelname = levelname

            return formatted
        else:
            return super().format(record)


def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    use_colors: bool = True,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        use_colors: Whether to use colored output in console
        log_format: Custom log format string
        date_format: Custom date format string

    Example:
        setup_logging(
            level=logging.DEBUG,
            log_file="logs/app.log",
            use_colors=True
        )
    """
    # Import settings here to avoid circular imports
    try:
        from app.config.settings import settings

        default_level = logging.DEBUG if settings.DEBUG else logging.INFO
    except ImportError:
        default_level = logging.INFO

    level = level or default_level

    # Default formats
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colors (use stderr to avoid polluting stdout for MCP stdio mode)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        fmt=log_format, datefmt=date_format, use_colors=use_colors
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Silence noisy libraries (optional)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Name of the logger (typically __name__ from the calling module)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    return logging.getLogger(name)


# Configure logging on module import with sensible defaults
# This ensures logging works even if setup_logging() is never called
if not logging.getLogger().handlers:
    setup_logging()
