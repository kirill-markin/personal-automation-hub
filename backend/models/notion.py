from pydantic import BaseModel


class NotionTaskCreate(BaseModel):
    title: str


class NotionTaskResponse(BaseModel):
    success: bool
    task_id: str 