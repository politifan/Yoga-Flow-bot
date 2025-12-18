import json
import os
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
BOT_DATA_DIR = BASE_DIR / "data"
DEFAULT_EXTERNAL_DATA_DIR = BASE_DIR.parent / "Yoga_Flow" / "data"


def detect_external_data_dir(env_var: str = "YOGA_DATA_DIR", strict: bool = False) -> Path:
    """
    Returns a data directory for shared files (e.g., user data from Yoga_Flow/data).
    Priority: env var -> Yoga_Flow/data -> bot's own data folder (if not strict).
    If strict=True and directory не найден, бросает ошибку.
    """
    env_value = os.getenv(env_var)
    if env_value:
        resolved = Path(env_value).expanduser().resolve()
        if strict and not resolved.exists():
            raise RuntimeError(f"Каталог данных {resolved} не найден. Задайте корректный {env_var}.")
        return resolved
    if DEFAULT_EXTERNAL_DATA_DIR.exists():
        return DEFAULT_EXTERNAL_DATA_DIR
    if strict:
        raise RuntimeError(
            f"Каталог данных {DEFAULT_EXTERNAL_DATA_DIR} не найден. "
            f"Укажите путь в переменной {env_var}."
        )
    return BOT_DATA_DIR


def load_json(name: str, default: Any, base_dir: Optional[Path] = None) -> Any:
    base = base_dir or BOT_DATA_DIR
    path = base / name
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, payload: Any, base_dir: Optional[Path] = None) -> None:
    base = base_dir or BOT_DATA_DIR
    path = base / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
