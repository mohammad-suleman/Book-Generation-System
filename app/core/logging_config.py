"""
Logging configuration - separate files for app logs, errors, and output
"""
import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logging():
    """
    Configure logging with 3 log files:
    - logs/app.log       : All application logs (INFO+)
    - logs/error.log     : Errors only (ERROR+)
    - logs/output.log    : Book generation output/results
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Root / app logger ---
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)
    app_logger.handlers.clear()

    # File handler - all logs
    app_fh = logging.FileHandler(log_dir / f"app_{date_str}.log", encoding="utf-8")
    app_fh.setLevel(logging.INFO)
    app_fh.setFormatter(fmt)
    app_logger.addHandler(app_fh)

    # File handler - errors only
    err_fh = logging.FileHandler(log_dir / f"error_{date_str}.log", encoding="utf-8")
    err_fh.setLevel(logging.ERROR)
    err_fh.setFormatter(fmt)
    app_logger.addHandler(err_fh)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    app_logger.addHandler(console)

    # --- Output logger (book generation results) ---
    output_logger = logging.getLogger("app.output")
    output_logger.setLevel(logging.INFO)
    output_logger.handlers.clear()
    output_logger.propagate = False  # don't duplicate to app.log

    out_fh = logging.FileHandler(log_dir / f"output_{date_str}.log", encoding="utf-8")
    out_fh.setLevel(logging.INFO)
    out_fh.setFormatter(fmt)
    output_logger.addHandler(out_fh)

    # Also show output on console
    out_console = logging.StreamHandler()
    out_console.setLevel(logging.INFO)
    out_console.setFormatter(fmt)
    output_logger.addHandler(out_console)

    return app_logger


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
