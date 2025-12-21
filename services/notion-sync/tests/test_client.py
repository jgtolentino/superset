"""Tests for Notion API client."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from notion_sync.client import NotionClient, NotionAPIError, RateLimitError
from notion_sync.config import Config
from notion_sync.models import NotionPage


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    with patch.dict("os.environ", {
        "NOTION_API_KEY": "test-key",
        "DATABRICKS_HOST": "https://test.databricks.net",
        "DATABRICKS_TOKEN": "test-token",
    }):
        return Config()


@pytest.fixture
def sample_page_response():
    """Sample Notion page API response."""
    return {
        "id": "page-123",
        "object": "page",
        "created_time": "2024-01-01T00:00:00.000Z",
        "last_edited_time": "2024-01-15T12:00:00.000Z",
        "archived": False,
        "parent": {
            "type": "database_id",
            "database_id": "db-456"
        },
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "plain_text": "Test Project"}]
            },
            "Status": {
                "id": "status",
                "type": "select",
                "select": {"name": "Active", "color": "green"}
            },
            "Budget": {
                "id": "budget",
                "type": "number",
                "number": 100000
            }
        }
    }


@pytest.fixture
def sample_query_response(sample_page_response):
    """Sample database query response."""
    return {
        "object": "list",
        "results": [sample_page_response],
        "has_more": False,
        "next_cursor": None
    }


class TestNotionPage:
    """Tests for NotionPage model."""

    def test_from_api_response(self, sample_page_response):
        """Test creating NotionPage from API response."""
        page = NotionPage.from_api_response(sample_page_response)

        assert page.page_id == "page-123"
        assert page.database_id == "db-456"
        assert page.archived is False
        assert page.last_edited_time.year == 2024

    def test_get_title_property(self, sample_page_response):
        """Test extracting title property."""
        page = NotionPage.from_api_response(sample_page_response)

        name = page.get_property_value("Name")
        assert name == "Test Project"

    def test_get_select_property(self, sample_page_response):
        """Test extracting select property."""
        page = NotionPage.from_api_response(sample_page_response)

        status = page.get_property_value("Status")
        assert status == "Active"

    def test_get_number_property(self, sample_page_response):
        """Test extracting number property."""
        page = NotionPage.from_api_response(sample_page_response)

        budget = page.get_property_value("Budget")
        assert budget == 100000

    def test_get_missing_property(self, sample_page_response):
        """Test extracting non-existent property."""
        page = NotionPage.from_api_response(sample_page_response)

        value = page.get_property_value("NonExistent")
        assert value is None

    def test_to_flat_dict(self, sample_page_response):
        """Test converting to flat dictionary."""
        page = NotionPage.from_api_response(sample_page_response)

        flat = page.to_flat_dict({
            "Name": "name",
            "Status": "status",
            "Budget": "budget_total",
        })

        assert flat["page_id"] == "page-123"
        assert flat["name"] == "Test Project"
        assert flat["status"] == "Active"
        assert flat["budget_total"] == 100000


class TestNotionClient:
    """Tests for NotionClient."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_database(self, mock_config, sample_query_response):
        """Test querying a database."""
        route = respx.post(
            "https://api.notion.com/v1/databases/db-123/query"
        ).mock(
            return_value=httpx.Response(200, json=sample_query_response)
        )

        async with NotionClient(mock_config) as client:
            result = await client.query_database("db-123")

        assert route.called
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_database_with_filter(self, mock_config, sample_query_response):
        """Test querying with time filter."""
        route = respx.post(
            "https://api.notion.com/v1/databases/db-123/query"
        ).mock(
            return_value=httpx.Response(200, json=sample_query_response)
        )

        filter_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        async with NotionClient(mock_config) as client:
            result = await client.query_database(
                "db-123",
                filter_after=filter_time
            )

        assert route.called
        # Verify filter was included in request
        request_body = route.calls[0].request.content
        assert b"last_edited_time" in request_body

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limit_handling(self, mock_config, sample_query_response):
        """Test rate limit retry behavior."""
        # First call returns 429, second succeeds
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json=sample_query_response),
            ]
        )

        async with NotionClient(mock_config) as client:
            result = await client.query_database("db-123")

        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error(self, mock_config):
        """Test API error handling."""
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            return_value=httpx.Response(
                400,
                json={"message": "Invalid database ID"}
            )
        )

        async with NotionClient(mock_config) as client:
            with pytest.raises(NotionAPIError) as exc_info:
                await client.query_database("db-123")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @respx.mock
    async def test_iter_database_pages(self, mock_config, sample_page_response):
        """Test iterating through database pages."""
        # Mock paginated response
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            side_effect=[
                httpx.Response(200, json={
                    "results": [sample_page_response],
                    "has_more": True,
                    "next_cursor": "cursor-1"
                }),
                httpx.Response(200, json={
                    "results": [sample_page_response],
                    "has_more": False,
                    "next_cursor": None
                }),
            ]
        )

        pages = []
        async with NotionClient(mock_config) as client:
            async for page in client.iter_database_pages("db-123"):
                pages.append(page)

        assert len(pages) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_health_check_success(self, mock_config):
        """Test health check when API is accessible."""
        respx.get("https://api.notion.com/v1/users/me").mock(
            return_value=httpx.Response(200, json={"id": "user-123"})
        )

        async with NotionClient(mock_config) as client:
            healthy = await client.health_check()

        assert healthy is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_health_check_failure(self, mock_config):
        """Test health check when API is not accessible."""
        respx.get("https://api.notion.com/v1/users/me").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        async with NotionClient(mock_config) as client:
            healthy = await client.health_check()

        assert healthy is False


class TestConfig:
    """Tests for configuration."""

    def test_valid_config(self):
        """Test loading valid configuration."""
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "valid-key",
            "DATABRICKS_HOST": "https://test.databricks.net",
            "DATABRICKS_TOKEN": "valid-token",
            "NOTION_PROJECTS_DB_ID": "db-123",
        }):
            config = Config()

            assert config.notion_api_key == "valid-key"
            assert config.databricks_host == "https://test.databricks.net"

            dbs = config.get_databases()
            assert len(dbs) == 1
            assert dbs[0].name == "projects"

    def test_suspicious_value_blocked(self):
        """Test that placeholder values are rejected."""
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "changeme",
            "DATABRICKS_HOST": "https://test.databricks.net",
            "DATABRICKS_TOKEN": "valid-token",
        }):
            with pytest.raises(ValueError) as exc_info:
                Config()

            assert "suspicious default value" in str(exc_info.value)

    def test_get_databases_empty(self):
        """Test getting databases when none configured."""
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "valid-key",
            "DATABRICKS_HOST": "https://test.databricks.net",
            "DATABRICKS_TOKEN": "valid-token",
        }):
            config = Config()
            dbs = config.get_databases()

            assert len(dbs) == 0

    def test_get_databases_all(self):
        """Test getting all configured databases."""
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "valid-key",
            "DATABRICKS_HOST": "https://test.databricks.net",
            "DATABRICKS_TOKEN": "valid-token",
            "NOTION_PROGRAMS_DB_ID": "db-1",
            "NOTION_PROJECTS_DB_ID": "db-2",
            "NOTION_BUDGET_LINES_DB_ID": "db-3",
            "NOTION_RISKS_DB_ID": "db-4",
            "NOTION_ACTIONS_DB_ID": "db-5",
        }):
            config = Config()
            dbs = config.get_databases()

            assert len(dbs) == 5
            names = [db.name for db in dbs]
            assert "programs" in names
            assert "projects" in names
            assert "budget_lines" in names
            assert "risks" in names
            assert "actions" in names
