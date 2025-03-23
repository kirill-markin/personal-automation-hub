from notion_client import Client
from typing import Dict, Any, cast

from backend.core.config import settings


class NotionService:
    def __init__(self) -> None:
        self.client = Client(auth=settings.NOTION_API_KEY)
        self.database_id = settings.NOTION_DATABASE_ID

    def create_task(self, title: str) -> str:
        """Create a task in Notion database and return the page ID."""
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        return cast(Dict[str, Any], response)["id"]


notion_service = NotionService() 