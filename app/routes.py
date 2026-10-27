import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from .config import DEFAULT_BASE_URL, DEFAULT_MODEL, get_api_key, load_config, make_client, save_config
from .schemas import ChatBody, ConfigBody

router = APIRouter(prefix="/api")


@router.get("/config")
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


@router.post("/config")
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


@router.get("/models")
def list_models():
    key = get_api_key()
    if not key:
        raise HTTPException(400, "未配置 API Key")
    client = OpenAI(api_key=key, base_url=load_config().get("base_url", DEFAULT_BASE_URL))
    try:
        return {"models": sorted(m.id for m in client.models.list())}
    except Exception as e:
        raise HTTPException(502, f"获取模型列表失败: {e}")


@router.post("/chat")
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
