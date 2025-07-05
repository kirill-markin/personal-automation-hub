from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from backend.core.security import validate_api_key
from backend.models.notion import NotionTaskCreate, NotionTaskResponse
from backend.services.notion.client import notion_service

router = APIRouter()


@router.post(
    "/notion-personal/create-task",
    response_model=NotionTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notion_personal_task(
    task: NotionTaskCreate,
    api_key: Annotated[str, Depends(validate_api_key)],
) -> NotionTaskResponse:
    """
    Create a task in Notion database with optional body content.
    """
    try:
        task_id = notion_service.create_task(title=task.title, body=task.body)
        return NotionTaskResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating Notion task: {str(e)}",
        ) 