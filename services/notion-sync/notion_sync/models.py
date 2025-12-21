"""Pydantic models for Notion data structures."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotionUser(BaseModel):
    """Notion user reference."""

    id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    object: str = "user"


class NotionRichText(BaseModel):
    """Notion rich text element."""

    type: str
    plain_text: str
    href: Optional[str] = None


class NotionProperty(BaseModel):
    """Base model for Notion properties."""

    id: str
    type: str


class NotionPage(BaseModel):
    """Normalized Notion page representation."""

    page_id: str = Field(..., description="Notion page UUID")
    database_id: str = Field(..., description="Parent database UUID")
    last_edited_time: datetime = Field(..., description="Last modification time")
    created_time: datetime = Field(..., description="Creation time")
    archived: bool = Field(default=False, description="Is page archived")
    properties: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(
        default_factory=dict, description="Full API response"
    )

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "NotionPage":
        """Create NotionPage from Notion API response."""
        # Extract parent database ID
        parent = data.get("parent", {})
        database_id = parent.get("database_id", "")

        return cls(
            page_id=data["id"],
            database_id=database_id,
            last_edited_time=datetime.fromisoformat(
                data["last_edited_time"].replace("Z", "+00:00")
            ),
            created_time=datetime.fromisoformat(
                data["created_time"].replace("Z", "+00:00")
            ),
            archived=data.get("archived", False),
            properties=data.get("properties", {}),
            raw_payload=data,
        )

    def get_property_value(self, prop_name: str) -> Any:
        """Extract value from a Notion property."""
        prop = self.properties.get(prop_name)
        if not prop:
            return None

        prop_type = prop.get("type")

        if prop_type == "title":
            title_array = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_array)

        elif prop_type == "rich_text":
            text_array = prop.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in text_array)

        elif prop_type == "number":
            return prop.get("number")

        elif prop_type == "select":
            select = prop.get("select")
            return select.get("name") if select else None

        elif prop_type == "multi_select":
            return [s.get("name") for s in prop.get("multi_select", [])]

        elif prop_type == "date":
            date = prop.get("date")
            return date.get("start") if date else None

        elif prop_type == "checkbox":
            return prop.get("checkbox", False)

        elif prop_type == "email":
            return prop.get("email")

        elif prop_type == "phone_number":
            return prop.get("phone_number")

        elif prop_type == "url":
            return prop.get("url")

        elif prop_type == "relation":
            return [r.get("id") for r in prop.get("relation", [])]

        elif prop_type == "people":
            return [p.get("id") for p in prop.get("people", [])]

        elif prop_type == "formula":
            formula = prop.get("formula", {})
            formula_type = formula.get("type")
            return formula.get(formula_type)

        elif prop_type == "rollup":
            rollup = prop.get("rollup", {})
            rollup_type = rollup.get("type")
            if rollup_type == "array":
                return rollup.get("array", [])
            return rollup.get(rollup_type)

        elif prop_type == "status":
            status = prop.get("status")
            return status.get("name") if status else None

        else:
            # Return raw for unknown types
            return prop

    def to_flat_dict(self, field_mappings: dict[str, str]) -> dict[str, Any]:
        """Convert to flat dictionary using field mappings."""
        result: dict[str, Any] = {
            "page_id": self.page_id,
            "database_id": self.database_id,
            "last_edited_time": self.last_edited_time.isoformat(),
            "created_time": self.created_time.isoformat(),
            "is_archived": self.archived,
        }

        for notion_name, target_name in field_mappings.items():
            value = self.get_property_value(notion_name)
            result[target_name] = value

        return result


class SyncWatermark(BaseModel):
    """Tracks sync progress for a database."""

    database_id: str
    database_name: str
    last_synced_time: datetime
    last_sync_run: datetime
    pages_synced: int = 0


class BronzeRecord(BaseModel):
    """Record format for bronze.notion_raw_pages table."""

    page_id: str
    database_id: str
    database_name: str
    last_edited_time: datetime
    properties: dict[str, str]
    raw_payload: str  # JSON string
    synced_at: datetime


class SyncResult(BaseModel):
    """Result of a sync operation."""

    database_id: str
    database_name: str
    pages_synced: int
    pages_skipped: int
    errors: list[str]
    duration_seconds: float
    success: bool
