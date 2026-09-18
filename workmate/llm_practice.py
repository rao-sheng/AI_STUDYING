import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

#question="解释什么是RAG？"
def ask_messages(messages:list[dict[str,str]]) ->str:
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("请在项目 .env 或环境变量中配置 DEEPSEEK_API_KEY")

    try:
        response = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "deepseek-flash",
            "messages": messages,
            "stream": False,
        },
        timeout=120.0,
        trust_env=False,   # 新增：不走系统代理 直接国内就行，但我开了代理，所以用这个禁止本文件代理
    )

        response.raise_for_status()

    except httpx.TimeoutException:
        print( "模型请求超时，请稍后再试。")
        raise
    except httpx.HTTPStatusError as exc:
        print( f"模型服务返回错误，状态码：{exc.response.status_code}")
        raise
    except httpx.RequestError as exc:
        print( f"请求发送或接收失败，错误类型：{type(exc).__name__}")
        raise
    else:
        data = response.json()
        usage=data["usage"]
        # print("输入TOKEN：",usage["prompt_tokens"])
        # print("输出token:",usage["completion_tokens"]
        #     )
        # print("合计TOKEN",usage["total_tokens"])
        answer = data["choices"][0]["message"]["content"]
        return  answer

def ask_model(question:str) ->str:
    messages=[
        {
            "role":"system",
            "content":"你是AI应用开发助手，请用简洁的中文回答"
        },
        {
            "role":"user",
            "content":question
        }

    ]
    return ask_messages(messages)

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "请用简洁中文回答。"},
        {"role": "user", "content": "我正在开发的项目叫 WorkMate。"},
    ]

    first_answer = ask_messages(messages)
    print("第一轮：", first_answer)

    messages.append({
        "role": "assistant",
        "content": first_answer,
    })

    messages.append({
        "role": "user",
        "content": "我的项目叫什么？",
    })

    second_answer = ask_messages(messages)
    print("第二轮：", second_answer)
