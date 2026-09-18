from store import get_messages,save_turn
from llm_practice import ask_messages
from datetime import datetime,timezone


def reply_with_history(
        conversation_id:str,
        question:str
) ->str:
    history=get_messages(conversation_id)
    #因为初始化表不带system,所以必须要初始化system
    messages=[{
        "role":"system",
        "content":"你是AI开发助手，请用简洁中文回答"
        }]
    messages.extend(history)
    messages.append({
        "role":"user",
        "content":question
    })
    answer=ask_messages(messages)
    now=datetime.now(timezone.utc).isoformat()
    save_turn(
        conversation_id,
        question,
        answer,
        now
    )
    return answer
