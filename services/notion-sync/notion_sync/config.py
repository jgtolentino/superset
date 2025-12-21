"""Configuration management for Notion Sync service."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig:
    """Configuration for a single Notion database."""

    def __init__(
        self,
        id: str,
        name: str,
        sync_interval: int = 300,
        field_mappings: Optional[dict[str, str]] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.sync_interval = sync_interval
        self.field_mappings = field_mappings or {}


class Config(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Notion settings
    notion_api_key: str = Field(
        ...,
        description="Notion internal integration token",
    )
    notion_api_version: str = Field(
        default="2022-06-28",
        description="Notion API version",
    )
    notion_base_url: str = Field(
        default="https://api.notion.com/v1",
        description="Notion API base URL",
    )

    # Database IDs (from environment)
    notion_programs_db_id: Optional[str] = Field(
        default=None,
        description="Notion Programs database ID",
    )
    notion_projects_db_id: Optional[str] = Field(
        default=None,
        description="Notion Projects database ID",
    )
    notion_budget_lines_db_id: Optional[str] = Field(
        default=None,
        description="Notion Budget Lines database ID",
    )
    notion_risks_db_id: Optional[str] = Field(
        default=None,
        description="Notion Risks database ID",
    )
    notion_actions_db_id: Optional[str] = Field(
        default=None,
        description="Notion Actions database ID",
    )

    # Databricks settings
    databricks_host: str = Field(
        ...,
        description="Databricks workspace URL",
    )
    databricks_token: str = Field(
        ...,
        description="Databricks personal access token",
    )
    databricks_http_path: Optional[str] = Field(
        default=None,
        description="Databricks SQL warehouse HTTP path",
    )
    databricks_catalog: str = Field(
        default="main",
        description="Unity Catalog name",
    )

    # Sync settings
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of pages to fetch per request",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for API calls",
    )
    backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff factor",
    )
    rate_limit_delay: float = Field(
        default=0.34,
        ge=0.0,
        description="Delay between API calls (Notion: 3 req/sec)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_json: bool = Field(
        default=True,
        description="Use JSON logging format",
    )

    @field_validator("notion_api_key", "databricks_token")
    @classmethod
    def validate_not_placeholder(cls, v: str, info) -> str:
        """Ensure credentials are not placeholder values."""
        placeholders = ["changeme", "password", "secret", "your-key-here", "xxx"]
        if v.lower() in placeholders:
            raise ValueError(
                f"BLOCKED: suspicious default value in {info.field_name}"
            )
        return v

    def get_databases(self) -> list[DatabaseConfig]:
        """Get list of configured databases to sync."""
        databases = []

        if self.notion_programs_db_id:
            databases.append(
                DatabaseConfig(
                    id=self.notion_programs_db_id,
                    name="programs",
                    field_mappings={
                        "Name": "name",
                        "Owner": "owner",
                        "Start Date": "start_date",
                        "End Date": "end_date",
                        "Status": "status",
                    },
                )
            )

        if self.notion_projects_db_id:
            databases.append(
                DatabaseConfig(
                    id=self.notion_projects_db_id,
                    name="projects",
                    field_mappings={
                        "Name": "name",
                        "Program": "program_id",
                        "Budget Total": "budget_total",
                        "Currency": "currency",
                        "Start Date": "start_date",
                        "End Date": "end_date",
                        "Status": "status",
                        "Priority": "priority",
                        "Owner": "owner",
                    },
                )
            )

        if self.notion_budget_lines_db_id:
            databases.append(
                DatabaseConfig(
                    id=self.notion_budget_lines_db_id,
                    name="budget_lines",
                    field_mappings={
                        "Project": "project_id",
                        "Category": "category",
                        "Vendor": "vendor",
                        "Amount": "amount",
                        "Committed Date": "committed_date",
                        "Invoice Date": "invoice_date",
                        "Paid Date": "paid_date",
                        "Actual Amount": "actual_amount",
                        "Notes": "notes",
                    },
                )
            )

        if self.notion_risks_db_id:
            databases.append(
                DatabaseConfig(
                    id=self.notion_risks_db_id,
                    name="risks",
                    field_mappings={
                        "Title": "title",
                        "Project": "project_id",
                        "Severity": "severity",
                        "Probability": "probability",
                        "Status": "status",
                        "Mitigation": "mitigation",
                        "Owner": "owner",
                    },
                )
            )

        if self.notion_actions_db_id:
            databases.append(
                DatabaseConfig(
                    id=self.notion_actions_db_id,
                    name="actions",
                    field_mappings={
                        "Title": "title",
                        "Project": "project_id",
                        "Assignee": "assignee",
                        "Due Date": "due_date",
                        "Status": "status",
                        "Source": "source",
                    },
                )
            )

        return databases

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load configuration from YAML file with env var substitution."""
        import os
        import re

        with open(path) as f:
            content = f.read()

        # Substitute ${ENV_VAR} patterns
        def replace_env(match: re.Match[str]) -> str:
            var_name = match.group(1)
            value = os.environ.get(var_name, "")
            if not value:
                raise ValueError(f"BLOCKED: missing env var {var_name}")
            return value

        content = re.sub(r"\$\{(\w+)\}", replace_env, content)
        data = yaml.safe_load(content)

        return cls(**data)
