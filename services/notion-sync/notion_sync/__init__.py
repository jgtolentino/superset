"""Notion Sync Service - Sync Notion databases to Databricks lakehouse."""

__version__ = "0.1.0"

from notion_sync.config import Config
from notion_sync.sync import NotionSyncer

__all__ = ["Config", "NotionSyncer", "__version__"]
