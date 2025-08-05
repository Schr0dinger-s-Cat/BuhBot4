# WEEEK.py
import os

import httpx
import asyncio
import logging
from dotenv import load_dotenv, set_key
from typing import Optional

# --- Настройка логгирования ---
logger = logging.getLogger("WEEEK_INIT")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("weeek_integration.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# --- Загрузка переменных окружения ---
load_dotenv()
ENV_PATH = ".env"
BASE_URL = "https://api.weeek.net/public/v1/"
API_KEY = os.getenv("WEEEK_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

PROJECT_NAME = "Бух. Задачи. Бэклог"
BOARD_NAME = "Бэклог"
COLUMN_NAME = "Бэклог. !НЕ ДВИГАТЬ!"


async def handle_response(response: httpx.Response, action: str):
    try:
        data = response.json()
    except Exception:
        logger.error(f"{action}: невалидный JSON")
        raise Exception(f"{action}: невалидный JSON")

    if response.status_code >= 400:
        logger.error(f"{action}: ошибка {response.status_code} — {data.get('message')}")
        raise Exception(f"{action}: ошибка {response.status_code} — {data.get('message')}")

    return data


async def find_or_create_project(client: httpx.AsyncClient) -> int:
    logger.info(f"Поиск или создание проекта '{PROJECT_NAME}'")
    resp = await client.get(f"{BASE_URL}tm/projects", headers=headers)
    data = await handle_response(resp, "Получение проектов")

    for project in data.get("projects", []):
        if project.get("name") == PROJECT_NAME:
            logger.info(f"Проект найден: ID {project['id']}")
            return project["id"]

    payload = {
        "name": PROJECT_NAME,
        "isPrivate": False,
        "description": "Автоматически созданный проект",
        "portfolioId": None
    }
    resp = await client.post(f"{BASE_URL}tm/projects", json=payload, headers=headers)
    data = await handle_response(resp, "Создание проекта")
    project = data.get("project")
    if not project or "id" not in project:
        raise Exception("Ошибка: проект создан, но ID не получен")
    logger.info(f"Проект создан: ID {project['id']}")
    return project["id"]


async def find_or_create_board(client: httpx.AsyncClient, project_id: int) -> dict:
    logger.info(f"Поиск или создание доски '{BOARD_NAME}'")
    resp = await client.get(f"{BASE_URL}tm/boards", headers=headers, params={"projectId": project_id})
    data = await handle_response(resp, "Получение досок")
    boards = data if isinstance(data, list) else data.get("boards", data.get("data", []))

    for board in boards:
        if board.get("name") == BOARD_NAME:
            logger.info(f"Доска найдена: ID {board['id']}")
            return board

    payload = {
        "name": BOARD_NAME,
        "projectId": project_id,
        "description": "Доска для задач",
        "color": "#3498db"
    }
    resp = await client.post(f"{BASE_URL}tm/boards", json=payload, headers=headers)
    await handle_response(resp, "Создание доски")

    resp = await client.get(f"{BASE_URL}tm/boards", headers=headers, params={"projectId": project_id})
    data = await handle_response(resp, "Повторный поиск доски")
    for board in data.get("boards", data.get("data", [])):
        if board.get("name") == BOARD_NAME:
            logger.info(f"Доска подтверждена: ID {board['id']}")
            return board

    raise Exception("Не удалось создать доску")


async def ensure_backlog_column(client: httpx.AsyncClient, board_id: int):
    logger.info("Проверка наличия и позиции столбца 'Бэклог. !НЕ РЕДАКТИРОВАТЬ НАЗВАНИЕ!'")
    resp = await client.get(f"{BASE_URL}tm/board-columns", headers=headers, params={"boardId": board_id})
    data = await handle_response(resp, "Получение столбцов")
    columns = data.get("boardColumns", [])
    column = next((c for c in columns if c.get("name") == COLUMN_NAME), None)

    if column:
        if columns[0]["id"] != column["id"]:
            logger.info("Столбец найден, но не в начале. Перемещаем...")
            move_url = f"{BASE_URL}tm/board-columns/{column['id']}/move"
            await client.post(move_url, json={"upperBoardColumnId": None}, headers=headers)
            logger.info("Столбец перемещён в начало")
        else:
            logger.info("Столбец уже на первой позиции")
    else:
        logger.info("Столбец не найден. Создаём...")
        payload = {
            "name": COLUMN_NAME,
            "boardId": board_id
        }
        resp = await client.post(f"{BASE_URL}tm/board-columns", json=payload, headers=headers)
        col_data = await handle_response(resp, "Создание столбца")
        column_id = col_data.get("boardColumn", {}).get("id")

        if column_id is not None:
            logger.info("Столбец создан. Перемещаем в начало...")
            await client.post(f"{BASE_URL}tm/board-columns/{column_id}/move", json={"upperBoardColumnId": None}, headers=headers)
            logger.info("Столбец перемещён в начало")


def update_env_variable(key: str, value: str):
    os.environ[key] = value
    set_key(ENV_PATH, key, value)
    logger.info(f".env обновлён: {key} = {value}")


async def initialize_weeek_data():
    async with httpx.AsyncClient(timeout=15.0) as client:
        project_id = await find_or_create_project(client)
        board = await find_or_create_board(client, project_id)
        await ensure_backlog_column(client, board["id"])

        update_env_variable("WEEEK_PROJECT_ID", str(project_id))
        update_env_variable("WEEEK_BOARD_ID", str(board["id"]))

        return project_id, board["id"]


# --------------------------
# Новый функционал: создание задач
# --------------------------

async def create_task_minimal(client: httpx.AsyncClient, title: str, description: str, project_id: int, board_column_id: int) -> int:
    payload = {
        "title": title,
        "description": description,
        "locations": [{
            "projectId": project_id,
            "boardColumnId": board_column_id
        }],
        "type": "action"
    }
    resp = await client.post(f"{BASE_URL}tm/tasks", json=payload, headers=headers)
    data = await handle_response(resp, "Создание задачи")
    return data["task"]["id"]


async def get_task_details(client: httpx.AsyncClient, task_id: int) -> dict:
    resp = await client.get(f"{BASE_URL}tm/tasks/{task_id}", headers=headers)
    data = await handle_response(resp, f"Получение задачи {task_id}")
    return data["task"]

async def get_custom_field_from_task(task_data: dict, field_name: str) -> Optional[str]:
    for field in task_data.get("customFields", []):
        if field.get("name") == field_name:
            return field.get("id")
    return None


async def create_custom_field(client: httpx.AsyncClient, name: str, field_type: str = "text") -> str:
    payload = {
        "name": name,
        "type": field_type,
        "description": "Автоматически созданное поле для хранения информации о файлах"
    }
    resp = await client.post(f"{BASE_URL}tm/custom-fields", json=payload, headers=headers)
    data = await handle_response(resp, f"Создание кастомного поля '{name}'")
    return data.get("customField", {}).get("id")


async def update_task_with_files_field(client: httpx.AsyncClient, task_data: dict, files_field_id: str, files_info: str):
    payload = {
        "title": task_data["title"],
        "type": task_data["type"],
        "locations": task_data["locations"],
        "description": task_data.get("description", ""),
        "customFields": {
            files_field_id: files_info
        }
    }
    task_id = task_data["id"]
    resp = await client.put(f"{BASE_URL}tm/tasks/{task_id}", json=payload, headers=headers)
    await handle_response(resp, f"Обновление задачи {task_id} с полем 'Файлы'")


async def create_weeek_task(title: str, description: str, files_info: str):
    try:
        project_id = int(os.getenv("WEEEK_PROJECT_ID"))
        board_id = int(os.getenv("WEEEK_BOARD_ID"))

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{BASE_URL}tm/board-columns", headers=headers, params={"boardId": board_id})
            data = await handle_response(resp, "Получение колонок доски")
            columns = data.get("boardColumns", [])
            column = next((c for c in columns if c.get("name") == COLUMN_NAME), None)
            if not column:
                raise Exception("Колонка 'Бэклог' не найдена")

            task_id = await create_task_minimal(client, title, description, project_id, column["id"])
            task_data = await get_task_details(client, task_id)

            logger.info(f"Задача создана и дополнена полем 'Файлы': ID {task_id}")
            return task_id

    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {str(e)}")
        raise
