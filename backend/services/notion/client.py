from notion_client import Client
from typing import Dict, List, Any, Optional, cast

from backend.core.config import settings


class NotionService:
    def __init__(self) -> None:
        self.client = Client(auth=settings.notion_api_key)
        self.database_id = settings.notion_database_id

    def create_task(self, title: str, body: Optional[str] = None) -> str:
        """Create a task in Notion database and return the page ID."""
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        
        # Create the page first
        page_response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        # Extract page ID from response - cast to Dict since we're using sync client
        page_id = cast(Dict[str, Any], page_response)["id"]
        
        # Add body content as paragraph block if provided
        if body:
            self._add_paragraph_block(page_id=page_id, text=body)
        
        return page_id
    
    def _add_paragraph_block(self, page_id: str, text: str) -> None:
        """Add a paragraph block to a page."""
        children: List[Dict[str, Any]] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": text
                            }
                        }
                    ]
                }
            }
        ]
        
        self.client.blocks.children.append(
            block_id=page_id,
            children=children
        )


notion_service = NotionService() 