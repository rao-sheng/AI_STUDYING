from chat_service import reply_with_history
#生成一个随机唯一的识别码
from uuid import uuid4
from store import init_db,get_messages

init_db()


conversation_id=str(uuid4())

answer=reply_with_history(
    conversation_id,
    "我的项目是WorkMate,请记住这个名字"
)
history=get_messages(conversation_id)

assert history==[
     {
        "role": "user",
        "content": "我的项目是WorkMate，请记住这个名字。",
    },
    {
        "role": "assistant",
        "content": answer,
    },
]
print("一轮消息保存")