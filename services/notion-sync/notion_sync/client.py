"""Notion API client with retry logic and rate limiting."""

import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from notion_sync.config import Config
from notion_sync.models import NotionPage

logger = structlog.get_logger()


class NotionAPIError(Exception):
    """Base exception for Notion API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(NotionAPIError):
    """Rate limit exceeded."""

    pass


class NotionClient:
    """Async client for Notion API with retry and rate limiting."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.base_url = config.notion_base_url
        self.headers = {
            "Authorization": f"Bearer {config.notion_api_key}",
            "Notion-Version": config.notion_api_version,
            "Content-Type": "application/json",
        }
        self._last_request_time: float = 0
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "NotionClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self) -> None:
        """Enforce rate limiting (Notion: 3 requests/second)."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make an API request with retry logic."""
        await self._rate_limit()

        if not self._client:
            raise NotionAPIError("Client not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        log = logger.bind(method=method, endpoint=endpoint)
        log.debug("Making Notion API request")

        try:
            response = await self._client.request(method, url, json=json)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "5"))
                log.warning("Rate limited", retry_after=retry_after)
                await asyncio.sleep(retry_after)
                raise RateLimitError("Rate limit exceeded", 429)

            log.error(
                "Notion API error",
                status_code=e.response.status_code,
                body=e.response.text[:500],
            )
            raise NotionAPIError(
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                e.response.status_code,
            )

    async def query_database(
        self,
        database_id: str,
        start_cursor: Optional[str] = None,
        filter_after: Optional[datetime] = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Query a Notion database."""
        body: dict[str, Any] = {
            "page_size": min(page_size, 100),  # Max 100 per Notion
        }

        if start_cursor:
            body["start_cursor"] = start_cursor

        if filter_after:
            body["filter"] = {
                "timestamp": "last_edited_time",
                "last_edited_time": {
                    "after": filter_after.isoformat(),
                },
            }

        # Sort by last_edited_time for consistent ordering
        body["sorts"] = [
            {
                "timestamp": "last_edited_time",
                "direction": "ascending",
            }
        ]

        return await self._request(
            "POST",
            f"/databases/{database_id}/query",
            json=body,
        )

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Get database metadata."""
        return await self._request("GET", f"/databases/{database_id}")

    async def iter_database_pages(
        self,
        database_id: str,
        since: Optional[datetime] = None,
    ) -> AsyncIterator[NotionPage]:
        """Iterate through all pages in a database."""
        has_more = True
        start_cursor: Optional[str] = None
        total_pages = 0

        log = logger.bind(database_id=database_id, since=since)
        log.info("Starting database iteration")

        while has_more:
            response = await self.query_database(
                database_id=database_id,
                start_cursor=start_cursor,
                filter_after=since,
                page_size=self.config.batch_size,
            )

            results = response.get("results", [])
            for page_data in results:
                total_pages += 1
                yield NotionPage.from_api_response(page_data)

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            log.debug(
                "Fetched page batch",
                batch_size=len(results),
                has_more=has_more,
                total_so_far=total_pages,
            )

        log.info("Completed database iteration", total_pages=total_pages)

    async def create_page(
        self,
        database_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new page in a database."""
        body = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        return await self._request("POST", "/pages", json=body)

    async def update_page(
        self,
        page_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing page."""
        body = {"properties": properties}
        return await self._request("PATCH", f"/pages/{page_id}", json=body)

    async def health_check(self) -> bool:
        """Check if Notion API is accessible."""
        try:
            await self._request("GET", "/users/me")
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
