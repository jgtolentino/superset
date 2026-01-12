#!/usr/bin/env python3
"""
Skill: fetch_tableau_gallery_index
Intent: Scrape Tableau Public gallery pages to extract dashboard listings

Fetches dashboard listings from Tableau Public gallery pages, extracting
metadata like title, URL, author, tags, and view counts.
"""

import httpx
import json
import re
from typing import Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, parse_qs


@dataclass
class DashboardEntry:
    """Represents a Tableau Public dashboard entry."""
    title: str
    url: str
    author: str
    tags: list[str]
    thumbnail_url: Optional[str]
    view_count: int
    workbook_id: str


class TableauGalleryFetcher:
    """Fetches dashboard listings from Tableau Public galleries."""

    BASE_URL = "https://public.tableau.com"
    GALLERY_API = "https://public.tableau.com/api/gallery"
    SEARCH_API = "https://public.tableau.com/api/search/query"

    # Category mappings for Tableau Public
    CATEGORY_PATHS = {
        "business": "business-dashboards",
        "finance": "finance",
        "sales": "sales",
        "marketing": "marketing",
        "operations": "operations",
        "hr": "human-resources",
        "healthcare": "healthcare",
        "government": "government",
        "education": "education",
        "sports": "sports",
        "entertainment": "entertainment",
    }

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TableauScraper/1.0)",
                "Accept": "application/json, text/html",
            }
        )

    def fetch_gallery_index(
        self,
        gallery_url: str,
        max_results: int = 50,
        category_filter: Optional[str] = None
    ) -> dict:
        """
        Fetch dashboard listings from a Tableau Public gallery.

        Args:
            gallery_url: Tableau Public gallery URL
            max_results: Maximum number of results to return
            category_filter: Optional category filter

        Returns:
            Dict with 'dashboards' list and metadata
        """
        dashboards = []

        # Try API-based fetching first
        try:
            dashboards = self._fetch_via_api(gallery_url, max_results, category_filter)
        except Exception as api_error:
            print(f"API fetch failed: {api_error}, falling back to HTML scraping")

        # Fall back to HTML scraping if API fails
        if not dashboards:
            try:
                dashboards = self._fetch_via_html_scraping(gallery_url, max_results)
            except Exception as html_error:
                print(f"HTML scraping failed: {html_error}")

        # Apply category filter if specified
        if category_filter and dashboards:
            category_lower = category_filter.lower()
            dashboards = [
                d for d in dashboards
                if any(category_lower in tag.lower() for tag in d.get("tags", []))
                or category_lower in d.get("title", "").lower()
            ]

        return {
            "dashboards": dashboards[:max_results],
            "total_found": len(dashboards),
            "source_url": gallery_url,
            "category_filter": category_filter,
        }

    def _fetch_via_api(
        self,
        gallery_url: str,
        max_results: int,
        category_filter: Optional[str]
    ) -> list[dict]:
        """Fetch via Tableau Public API."""
        dashboards = []

        # Determine category from URL
        category = self._extract_category_from_url(gallery_url)

        # Build API request
        params = {
            "count": min(max_results, 100),
            "start": 0,
            "galleryType": "viz",
        }

        if category:
            params["category"] = category

        # Try gallery API
        try:
            response = self.client.get(self.GALLERY_API, params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    dashboards.append(self._parse_api_item(item))
        except Exception:
            pass

        # Try search API as fallback
        if not dashboards:
            search_params = {
                "query": category_filter or category or "business",
                "count": max_results,
                "type": "vizzes",
            }
            try:
                response = self.client.get(self.SEARCH_API, params=search_params)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("results", []):
                        dashboards.append(self._parse_search_item(item))
            except Exception:
                pass

        return dashboards

    def _fetch_via_html_scraping(self, gallery_url: str, max_results: int) -> list[dict]:
        """Fetch by scraping HTML gallery pages."""
        dashboards = []

        response = self.client.get(gallery_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch gallery: HTTP {response.status_code}")

        html = response.text

        # Extract embedded JSON data (Tableau uses React with embedded state)
        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', html, re.DOTALL)
        if json_match:
            try:
                state = json.loads(json_match.group(1))
                vizzes = state.get("gallery", {}).get("vizzes", [])
                for viz in vizzes[:max_results]:
                    dashboards.append(self._parse_state_viz(viz))
            except json.JSONDecodeError:
                pass

        # Fall back to regex-based extraction
        if not dashboards:
            # Extract viz cards from HTML
            viz_pattern = r'<a[^>]*href="(/app/profile/[^/]+/viz/[^"]+)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</div>'
            matches = re.findall(viz_pattern, html, re.DOTALL | re.IGNORECASE)

            for url_path, title in matches[:max_results]:
                full_url = urljoin(self.BASE_URL, url_path)
                workbook_id = self._extract_workbook_id(url_path)
                dashboards.append({
                    "title": title.strip(),
                    "url": full_url,
                    "author": self._extract_author_from_path(url_path),
                    "tags": [],
                    "thumbnail_url": None,
                    "view_count": 0,
                    "workbook_id": workbook_id,
                })

        return dashboards

    def _parse_api_item(self, item: dict) -> dict:
        """Parse item from gallery API response."""
        return {
            "title": item.get("title", item.get("name", "Untitled")),
            "url": f"{self.BASE_URL}/app/profile/{item.get('authorUsername', 'unknown')}/viz/{item.get('workbookRepoUrl', '')}",
            "author": item.get("authorDisplayName", item.get("authorUsername", "Unknown")),
            "tags": item.get("tags", []),
            "thumbnail_url": item.get("thumbnailUrl", item.get("thumbnail")),
            "view_count": item.get("viewCount", item.get("numberOfViews", 0)),
            "workbook_id": item.get("workbookId", item.get("id", "")),
        }

    def _parse_search_item(self, item: dict) -> dict:
        """Parse item from search API response."""
        return {
            "title": item.get("title", "Untitled"),
            "url": item.get("url", f"{self.BASE_URL}/views/{item.get('id', '')}"),
            "author": item.get("author", {}).get("displayName", "Unknown"),
            "tags": item.get("tags", []),
            "thumbnail_url": item.get("thumbnailUrl"),
            "view_count": item.get("viewCount", 0),
            "workbook_id": item.get("workbookId", item.get("id", "")),
        }

    def _parse_state_viz(self, viz: dict) -> dict:
        """Parse viz from embedded React state."""
        return {
            "title": viz.get("title", viz.get("name", "Untitled")),
            "url": f"{self.BASE_URL}/views/{viz.get('viewUrl', viz.get('id', ''))}",
            "author": viz.get("author", {}).get("displayName", "Unknown"),
            "tags": viz.get("tags", []),
            "thumbnail_url": viz.get("thumbnail", {}).get("url"),
            "view_count": viz.get("viewCount", 0),
            "workbook_id": viz.get("workbookId", viz.get("id", "")),
        }

    def _extract_category_from_url(self, url: str) -> Optional[str]:
        """Extract category from gallery URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        for part in path_parts:
            for category, path in self.CATEGORY_PATHS.items():
                if path in part.lower() or category in part.lower():
                    return category
        return None

    def _extract_workbook_id(self, url_path: str) -> str:
        """Extract workbook ID from URL path."""
        parts = url_path.strip("/").split("/")
        if "viz" in parts:
            idx = parts.index("viz")
            if idx + 1 < len(parts):
                return parts[idx + 1].split("/")[0]
        return ""

    def _extract_author_from_path(self, url_path: str) -> str:
        """Extract author username from URL path."""
        parts = url_path.strip("/").split("/")
        if "profile" in parts:
            idx = parts.index("profile")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return "Unknown"

    def close(self):
        """Close HTTP client."""
        self.client.close()


# =============================================================================
# SKILL HANDLER
# =============================================================================
async def handle(inputs: dict) -> dict:
    """
    Skill handler for fetch_tableau_gallery_index.

    Args:
        inputs: Dict with gallery_url, max_results, category_filter

    Returns:
        Dict with dashboards list
    """
    gallery_url = inputs.get("gallery_url")
    if not gallery_url:
        raise ValueError("gallery_url is required")

    max_results = inputs.get("max_results", 50)
    category_filter = inputs.get("category_filter")

    fetcher = TableauGalleryFetcher()
    try:
        result = fetcher.fetch_gallery_index(
            gallery_url=gallery_url,
            max_results=max_results,
            category_filter=category_filter
        )
        return result
    finally:
        fetcher.close()


# =============================================================================
# VALIDATION EXAMPLE
# =============================================================================
VALIDATION_EXAMPLE = {
    "input": {
        "gallery_url": "https://public.tableau.com/app/discover/business-dashboards",
        "max_results": 10,
        "category_filter": "sales"
    },
    "output": {
        "dashboards": [
            {
                "title": "Sales Performance Dashboard",
                "url": "https://public.tableau.com/app/profile/tableau/viz/SalesPerformance",
                "author": "Tableau",
                "tags": ["sales", "revenue", "kpi"],
                "thumbnail_url": "https://public.tableau.com/thumb/views/SalesPerformance/Dashboard",
                "view_count": 15420,
                "workbook_id": "SalesPerformance"
            },
            {
                "title": "Regional Sales Analysis",
                "url": "https://public.tableau.com/app/profile/analyst/viz/RegionalSales",
                "author": "analyst",
                "tags": ["sales", "regional", "analysis"],
                "thumbnail_url": "https://public.tableau.com/thumb/views/RegionalSales/Main",
                "view_count": 8230,
                "workbook_id": "RegionalSales"
            }
        ],
        "total_found": 2,
        "source_url": "https://public.tableau.com/app/discover/business-dashboards",
        "category_filter": "sales"
    }
}


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(handle(VALIDATION_EXAMPLE["input"]))
    print(json.dumps(result, indent=2))
