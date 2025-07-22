# loggers.py

import logging
import os
from datetime import datetime

# Цветной вывод в консоль
class ColorFormatter(logging.Formatter):
    COLORS = {
        'INFO': '\033[33m',     # Оранжевый
        'ERROR': '\033[91m',    # Красный
        'WARNING': '\033[93m',  # Желтый
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        msg = super().format(record)
        return f"{color}{record.levelname}: {msg}{self.COLORS['RESET']}"

def setup_user_not_friendly_logger():
    logger = logging.getLogger("telegram")
    logger.setLevel(logging.DEBUG)

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f"logs_RAW_{today}.txt")

    # File handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Console handler with color
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(ColorFormatter('%(asctime)s - %(name)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# Ручной логгер user-friendly
def log_user_friendly(msg: str):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(log_dir, f"logs_UF_{today}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(path, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")
