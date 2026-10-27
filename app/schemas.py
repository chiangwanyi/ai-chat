from pydantic import BaseModel


class ChatBody(BaseModel):
    messages: list[dict]
    model: str | None = None


class MessagesBody(BaseModel):
    history: list[dict] = []


class ConfigBody(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
