from pydantic import BaseModel,Field 
from datetime import datetime
from enum import Enum

class TaskStatus(str,Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

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



