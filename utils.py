# utils.py

import os
from datetime import datetime

_d_id = 0

def get_d_id():
    global _d_id
    return _d_id

def increase_d_id():
    global _d_id
    _d_id += 1

def reset_d_id():
    global _d_id
    _d_id = 0

def save_text_file(task_id: int, text: str, base_path='data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{task_id}_text.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def read_token():
    with open("token.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def save_rename_log(task_id: int, log_text: str, base_path='data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "rename.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(log_text)
    return path

def delete_task_files(task_id: int, base_path='data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(folder)


# utils.py

# utils.py

def build_task_card(task_id: int, user_name: str, created_at: str, full_text: str, files_list: list):
    # Очищаем текст от путей к файлам для названия
    clean_text = full_text.split('\n')[0].strip()
    title = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text

    # Очищаем текст задачи от путей к файлам
    task_text_lines = []
    for line in full_text.split('\n'):
        if not line.startswith('data\\') and line.strip():
            task_text_lines.append(line)
    cleaned_task_text = "\n".join(task_text_lines)

    text = (
            f"📝 Добавил: {user_name}\n"
            f"📅 Дата создания: {created_at}\n"
            f"📌 Название задачи: {title}\n\n"
            f"📃 Текст задачи:\n{cleaned_task_text}\n\n"
            f"📎 Файлы:\n"
            + "\n".join(files_list)
    )
    return text
