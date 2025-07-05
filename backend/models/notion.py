from pydantic import BaseModel
from typing import Optional


class NotionTaskCreate(BaseModel):
    title: str
    body: Optional[str] = None


class NotionTaskResponse(BaseModel):
    success: bool
    task_id: str 