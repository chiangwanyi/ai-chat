import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url="https://ai.shimiaocheng.top/v1",
)

def calculate(expression: str) -> str:
    """计算一个数学表达式。"""
    return str(eval(expression))

messages = [{"role": "system", "content": "你是一个友好、简洁的 AI 助手。"}]

response = client.chat.completions.create(
    model="deepseek-v4.1-flash",
    messages=[
        {
            "role": "user",
            "content": "请使用计算工具计算 12345 * 6789，不要心算。",
        }
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "计算数学表达式并返回结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "需要计算的数学表达式，例如 12345 * 6789",
                        }
                    },
                    "required": ["expression"],
                    "additionalProperties": False,
                },
            },
        }
    ],
    tool_choice="auto",
)

print(response.model_dump_json(indent=2))

