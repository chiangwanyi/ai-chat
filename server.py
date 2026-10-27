import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "config.json")
DEFAULT_BASE_URL = "https://ai.shimiaocheng.top/v1"
DEFAULT_MODEL = "deepseek-v4.1-flash"


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_api_key() -> str:
    return load_config().get("api_key") or os.environ.get("AI_API_KEY", "")


app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


class ChatBody(BaseModel):
    messages: list[dict]
    model: str | None = None


class ConfigBody(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


@app.get("/api/config")
def get_config():
    cfg = load_config()
    key = get_api_key()
    return {
        "base_url": cfg.get("base_url", DEFAULT_BASE_URL),
        "model": cfg.get("model", DEFAULT_MODEL),
        # 只回传掩码，前端永远拿不到完整密钥
        "has_key": bool(key),
        "key_masked": key[:4] + "****" + key[-4:] if len(key) > 8 else ("****" if key else ""),
    }


@app.post("/api/config")
def set_config(body: ConfigBody):
    cfg = load_config()
    if body.base_url:
        cfg["base_url"] = body.base_url.rstrip("/")
    if body.model:
        cfg["model"] = body.model
    if body.api_key:  # 空字符串表示不修改
        cfg["api_key"] = body.api_key
    save_config(cfg)
    return get_config()


@app.get("/api/models")
def list_models():
    key = get_api_key()
    if not key:
        raise HTTPException(400, "未配置 API Key")
    cfg = load_config()
    client = OpenAI(api_key=key, base_url=cfg.get("base_url", DEFAULT_BASE_URL))
    try:
        return {"models": sorted(m.id for m in client.models.list())}
    except Exception as e:
        raise HTTPException(502, f"获取模型列表失败: {e}")


def make_client() -> OpenAI:
    key = get_api_key()
    if not key:
        raise HTTPException(400, "未配置 API Key，请在设置中填写")
    cfg = load_config()
    return OpenAI(api_key=key, base_url=cfg.get("base_url", DEFAULT_BASE_URL))


@app.post("/api/chat")
def chat(body: ChatBody):
    client = make_client()
    model = body.model or load_config().get("model", DEFAULT_MODEL)

    def gen():
        stream = client.chat.completions.create(
            model=model,
            messages=body.messages,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
