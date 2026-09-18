from pydantic import BaseModel,Field 
from datetime import datetime
from enum import Enum

class TaskStatus(str,Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class AskResponse(BaseModel):
    question:str=Field(min_length=1,max_length=2000)


    
class TaskCreate(BaseModel):
    title:str=Field(...,min_length=1,max_length=80)
    description:str|None=Field(default=None,max_length=500)
    status:TaskStatus=TaskStatus.TODO

class TaskResponse(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime

class TaskUpdate(BaseModel):
    title:str|None=Field(default=None,min_length=1,max_length=80)
    description:str|None=Field(default=None,max_length=500)
    status:TaskStatus|None=None

class ChatRequest(BaseModel):
    conversation_id:str=Field(min_length=1,max_length=100)
    question:str=Field(min_length=1,max_length=2000)

class ChatResponse(BaseModel):
    answer:str
    conversation_id:str
