import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url="https://ai.shimiaocheng.top/v1",
)

messages = [
    {
        "role": "system",
        "content": """
你是一名资深的 AI 应用开发导师。

你的教学规则：
1. 面向有编程经验的开发者，不讲基础编程知识。
2. 每次只讲解一个新知识点。
3. 优先通过小型实战任务教学。
4. 解释 AI 特有的概念和设计决策。
5. 不要一次性给出完整项目。
6. 学员完成当前任务后，再进入下一步。
7. 使用中文回答，表达清晰、简洁。
""",
    }
]

while True:
    user_input = input("\n你：")
    if user_input.lower() == "exit":
        break
    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    stream = client.chat.completions.create(
        model="deepseek-v4.1-flash",
        messages=messages,
        stream=True,
    )
    print("\nAI：", end="", flush=True)
    answer = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)   # 去掉 !r
            answer += content
    print()
    messages.append({
        "role": "assistant",
        "content": answer,
    })
    # 删掉重复的第二次 append
print("聊天结束。")
