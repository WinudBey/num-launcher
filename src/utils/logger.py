"""Uygulama loglama modülü.

Bu modül DEBUG seviyesinde detaylı günlükleme sağlar.
Uygulama her başladığında eski günlük dosyasını temizler.
"""

import logging
import os
from typing import Optional

LOGGER_NAME = "NumpadBar"
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")


def setup_logger(log_to_console: bool = True) -> logging.Logger:
    """Uygulama günlüğünü hazırlar ve yapılandırır.

    Args:
        log_to_console: Konsol çıktısı verilip verilmeyeceğini belirler.

    Returns:
        logging.Logger: Yapılandırılmış günlük nesnesi.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    # Eski log dosyasını temizle (truncate)
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write("")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Önceki handler'ları temizle
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Dosya işleyicisi (File Handler)
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Konsol işleyicisi (Console Handler)
    if log_to_console:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.debug("Günlükleyici başlatıldı. Dosya: %s", LOG_FILE_PATH)
    return logger


def get_logger() -> logging.Logger:
    """Mevcut günlükleyiciyi döndürür veya yenisini oluşturur."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logger()
    return logger
