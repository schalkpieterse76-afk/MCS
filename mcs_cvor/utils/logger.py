import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "mcs_cvor") -> logging.Logger:
    log_dir = os.path.join(os.path.expanduser("~"), ".mcs_cvor", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "mcs_cvor.log")

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger
