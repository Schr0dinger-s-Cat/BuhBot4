# pathconf.py
import os
import sys
from pathlib import Path


def load_base_path():
    """Читает путь из path.txt или использует папку с exe/скриптом."""
    import sys

    if getattr(sys, 'frozen', False):  # Если исполняемый файл
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    path_file = base_dir / "path.txt"

    try:
        with open(path_file, "r", encoding="utf-8") as f:
            custom_path = f.read().strip()
            if custom_path and os.path.isabs(custom_path):
                return custom_path
    except (FileNotFoundError, UnicodeDecodeError):
        pass

    return str(base_dir / "Bot_Data")



BASE_PATH = load_base_path()
os.makedirs(BASE_PATH, exist_ok=True)