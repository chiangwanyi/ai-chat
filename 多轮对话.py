import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url="https://ai.shimiaocheng.top/v1",
)

messages = [{"role": "system", "content": "你是一个友好、简洁的 AI 助手。"}]

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
    response = client.chat.completions.create(
        model="deepseek-v4.1-flash",
        messages=messages,
    )
    answer = response.choices[0].message.content
    print(f"\nAI：{answer}")
    messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )
print("聊天结束。")
