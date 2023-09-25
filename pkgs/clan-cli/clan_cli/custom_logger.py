import datetime
import logging
from typing import Any


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\u001b[32m"
    blue = "\u001b[34m"

    @staticmethod
    def format_str(color: str) -> str:
        reset = "\x1b[0m"
        return f"{color}%(levelname)s{reset}:(%(filename)s:%(lineno)d): %(message)s"

    FORMATS = {
        logging.DEBUG: format_str(blue),
        logging.INFO: format_str(green),
        logging.WARNING: format_str(yellow),
        logging.ERROR: format_str(red),
        logging.CRITICAL: format_str(bold_red),
    }

    def format_time(self, record: Any, datefmt: Any = None) -> str:
        now = datetime.datetime.now()
        now = now.strftime("%H:%M:%S")
        return now

    def format(self, record: Any) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.formatTime = self.format_time
        return formatter.format(record)


def register(level: Any) -> None:
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(CustomFormatter())
    logging.basicConfig(level=level, handlers=[ch])
