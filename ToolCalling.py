import os
import json
from openai import OpenAI

# ==================== 1. 初始化客户端 ====================

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url="https://ai.shimiaocheng.top/v1",
)


# ==================== 2. 定义本地工具 ====================


def calculate(expression: str) -> str:
    """计算一个数学表达式。"""
    return str(eval(expression))


# ==================== 3. 告诉模型有哪些工具 ====================

tools = [
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
]


# ==================== 4. 发送用户问题 ====================

messages = [
    {
        "role": "user",
        "content": "请使用计算工具计算 12345 * 6789，不要心算。",
    }
]

response = client.chat.completions.create(
    model="deepseek-v4.1-flash",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message


# ==================== 5. 执行模型请求的工具 ====================

if message.tool_calls:
    # 将模型的工具调用请求加入对话历史
    messages.append(
        {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        }
    )

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "calculate":
            result = calculate(arguments["expression"])
        else:
            result = f"未知工具：{function_name}"

        print(f"工具名称：{function_name}")
        print(f"工具参数：{arguments}")
        print(f"工具结果：{result}")

        # 将工具执行结果交还给模型
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )

    # ==================== 6. 让模型生成最终回答 ====================

    final_response = client.chat.completions.create(
        model="deepseek-v4.1-flash",
        messages=messages,
        tools=tools,
    )

    print("\n模型最终回答：")
    print(final_response.choices[0].message.content)

else:
    # 如果模型没有请求调用工具，直接输出回答
    print("模型回答：")
    print(message.content)
