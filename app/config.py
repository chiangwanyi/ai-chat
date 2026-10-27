import json
import os
from pathlib import Path

from fastapi import HTTPException
from openai import OpenAI

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.json"
DEFAULT_BASE_URL = "https://ai.shimiaocheng.top/v1"
DEFAULT_MODEL = "deepseek-v4.1-flash"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_api_key() -> str:
    return load_config().get("api_key") or os.environ.get("AI_API_KEY", "")


def make_client() -> OpenAI:
    key = get_api_key()
    if not key:
        raise HTTPException(400, "未配置 API Key，请在设置中填写")
    cfg = load_config()
    return OpenAI(api_key=key, base_url=cfg.get("base_url", DEFAULT_BASE_URL))
