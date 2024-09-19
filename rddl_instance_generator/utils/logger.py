"""
Simple script to setup loggers for different files.
Allows for individual logging levels.
"""

import logging
from pathlib import Path


def setup_logger(
    name: str, log_path: Path, level: int = logging.WARNING
) -> logging.Logger:
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
