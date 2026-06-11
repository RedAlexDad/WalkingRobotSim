# walking_robot_utils/logging.py
"""
Centralized logging utility for WalkingRobotSim.

Usage:
    from walking_robot_utils.logging import get_logger

    log = get_logger("elevation_mapping.core")
    log.info("Map initialized")
    log.warn("Transform timeout")
    log.error("Kernel compilation failed")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

DEFAULT_LEVEL = logging.INFO
DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_DIR = "/tmp/walking_robot_sim"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5

COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARN": "\033[33m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "FATAL": "\033[35m",
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI color codes for console output."""

    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors

    def format(self, record):
        if self.use_colors and sys.stderr.isatty():
            color = COLORS.get(record.levelname, COLORS["RESET"])
            record.levelname = f"{color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


_loggers = {}
_configured = False


def configure(
    level=DEFAULT_LEVEL,
    log_dir=DEFAULT_LOG_DIR,
    max_bytes=DEFAULT_MAX_BYTES,
    backup_count=DEFAULT_BACKUP_COUNT,
    console=True,
    file=True,
    colors=True,
):
    global _configured
    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = ColoredFormatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT, colors)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root.addHandler(console_handler)

    if file:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "walking_robot_sim.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT))
        file_handler.setLevel(level)
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str, node=None, verbose: bool = False):
    if not _configured:
        configure()

    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(DEFAULT_LEVEL)
        _loggers[name] = LoggerAdapter(logger, verbose=verbose)

    return _loggers[name]


class LoggerAdapter:
    """Adapter with verbose support."""

    def __init__(self, logger: logging.Logger, verbose: bool = False):
        self._logger = logger
        self._verbose = verbose

    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value

    def debug(self, msg, *args, **kwargs):
        if self._verbose:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)


class ROS2LoggerHandler(logging.Handler):
    """Forward Python logging messages to ROS2 rclpy."""

    def __init__(self, node):
        super().__init__()
        self._node = node

    def emit(self, record):
        msg = self.format(record)
        try:
            if record.levelno >= logging.CRITICAL:
                self._node.get_logger().fatal(msg)
            elif record.levelno >= logging.ERROR:
                self._node.get_logger().error(msg)
            elif record.levelno >= logging.WARNING:
                self._node.get_logger().warn(msg)
            elif record.levelno >= logging.INFO:
                self._node.get_logger().info(msg)
            else:
                self._node.get_logger().debug(msg)
        except Exception:
            pass


def ros2_logger(name: str, node):
    logger = logging.getLogger(name)
    logger.addHandler(ROS2LoggerHandler(node))
    return logger
