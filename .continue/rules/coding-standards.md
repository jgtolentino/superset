# Coding Standards

> Style rules and conventions for the Notion Finance PPM Control Room

## General Principles

1. **Readability over cleverness** - Code should be easy to understand
2. **Explicit over implicit** - Be clear about intent
3. **Consistency over preference** - Follow established patterns
4. **Types everywhere** - No `any` in TypeScript, type hints in Python

## TypeScript / JavaScript

### Formatting

- Use Prettier with default settings
- 2-space indentation
- Single quotes for strings
- Trailing commas
- Semicolons required

```typescript
// Good
const fetchData = async (id: string): Promise<Data> => {
  const response = await client.get(`/api/data/${id}`);
  return response.data;
};

// Bad
const fetchData = async (id) => {
  const response = await client.get('/api/data/' + id)
  return response.data
}
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `KPICard.tsx` |
| Hooks | camelCase, `use` prefix | `useKPIData.ts` |
| Utilities | camelCase | `formatCurrency.ts` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES` |
| Types/Interfaces | PascalCase | `interface KPIResponse` |

### Component Structure

```typescript
// 1. Imports (external first, then internal)
import { useState } from 'react';
import { Button } from '@/components/ui/button';

// 2. Types
interface KPICardProps {
  title: string;
  value: number;
  unit: string;
}

// 3. Component
export function KPICard({ title, value, unit }: KPICardProps) {
  // 3a. Hooks
  const [isLoading, setIsLoading] = useState(false);

  // 3b. Handlers
  const handleClick = () => {
    // ...
  };

  // 3c. Render
  return (
    <div className="rounded-lg border p-4">
      <h3>{title}</h3>
      <span>{value} {unit}</span>
    </div>
  );
}
```

### API Route Structure

```typescript
// app/api/kpis/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

// 1. Schema
const QuerySchema = z.object({
  from: z.string(),
  to: z.string(),
});

// 2. Handler
export async function GET(request: NextRequest) {
  try {
    // 2a. Parse & validate
    const params = QuerySchema.parse(Object.fromEntries(
      request.nextUrl.searchParams
    ));

    // 2b. Business logic
    const data = await fetchKPIs(params);

    // 2c. Response
    return NextResponse.json({ data });
  } catch (error) {
    // 2d. Error handling
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', details: error.errors } },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Unknown error' } },
      { status: 500 }
    );
  }
}
```

## Python

### Formatting

- Use Black with default settings (88 line length)
- Use isort for import sorting
- 4-space indentation
- Double quotes for strings

```python
# Good
async def sync_database(self, database_id: str) -> int:
    """Sync a single Notion database to bronze."""
    watermark = await self._get_watermark(database_id)
    pages = await self._fetch_pages(database_id, since=watermark)
    return len(pages)

# Bad
async def sync_database(self, database_id):
    watermark = await self._get_watermark(database_id)
    pages = await self._fetch_pages(database_id, since=watermark)
    return len(pages)
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class NotionPage(BaseModel):
    page_id: str
    database_id: str
    last_edited_time: datetime
    properties: dict[str, str]


async def fetch_pages(
    database_id: str,
    since: Optional[datetime] = None,
) -> list[NotionPage]:
    """Fetch pages from Notion database."""
    ...
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `NotionSyncer` |
| Functions | snake_case | `sync_database` |
| Variables | snake_case | `page_count` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES` |
| Private | Leading underscore | `_internal_method` |

### Module Structure

```python
# 1. Standard library imports
import os
from datetime import datetime
from typing import Optional

# 2. Third-party imports
import httpx
from pydantic import BaseModel

# 3. Local imports
from notion_sync.config import Config

# 4. Constants
MAX_RETRIES = 3
BATCH_SIZE = 100

# 5. Classes
class NotionSyncer:
    """Syncer for Notion databases."""

    def __init__(self, config: Config) -> None:
        self.config = config

    async def sync(self) -> None:
        """Run sync for all databases."""
        ...

# 6. Functions (if not in class)
def format_timestamp(dt: datetime) -> str:
    """Format datetime for Notion API."""
    return dt.isoformat()
```

### Error Handling

```python
from notion_sync.exceptions import NotionAPIError, RateLimitError

async def fetch_with_retry(url: str) -> dict:
    """Fetch with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue
            raise NotionAPIError(f"HTTP {e.response.status_code}") from e
    raise RateLimitError("Max retries exceeded")
```

## SQL (Databricks)

### Formatting

- Keywords in UPPERCASE
- Table/column names in snake_case
- Indent subqueries
- One column per line in SELECT

```sql
-- Good
SELECT
    p.project_id,
    p.name AS project_name,
    SUM(bl.amount) AS total_budget,
    SUM(bl.actual_amount) AS total_actual,
    SUM(bl.actual_amount) - SUM(bl.amount) AS variance
FROM silver.notion_projects p
LEFT JOIN silver.notion_budget_lines bl
    ON p.project_id = bl.project_id
WHERE p.is_archived = false
GROUP BY p.project_id, p.name
ORDER BY variance DESC;

-- Bad
select p.project_id, p.name, sum(bl.amount), sum(bl.actual_amount)
from silver.notion_projects p left join silver.notion_budget_lines bl on p.project_id = bl.project_id
where p.is_archived = false group by p.project_id, p.name
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Tables | snake_case | `notion_projects` |
| Columns | snake_case | `budget_total` |
| Schemas | lowercase | `bronze`, `silver`, `gold` |
| Views | snake_case, `v_` prefix (optional) | `v_project_summary` |

### Table Standards

```sql
CREATE TABLE IF NOT EXISTS silver.notion_projects (
    -- Primary key first
    project_id STRING NOT NULL,

    -- Foreign keys next
    program_id STRING,

    -- Business columns
    name STRING NOT NULL,
    budget_total DECIMAL(18, 2),
    currency STRING DEFAULT 'USD',
    start_date DATE,
    end_date DATE,
    status STRING,
    priority STRING,

    -- Audit columns last
    is_archived BOOLEAN DEFAULT false,
    last_modified TIMESTAMP,
    synced_at TIMESTAMP DEFAULT current_timestamp(),

    -- Constraints
    PRIMARY KEY (project_id)
)
USING DELTA
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
);
```

## Testing Standards

### Python

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_sync_database_success():
    """Test successful database sync."""
    # Arrange
    syncer = NotionSyncer(config)
    syncer._fetch_pages = AsyncMock(return_value=[mock_page])
    syncer._write_to_bronze = AsyncMock()

    # Act
    count = await syncer.sync_database("db-123")

    # Assert
    assert count == 1
    syncer._write_to_bronze.assert_called_once()
```

### TypeScript

```typescript
import { render, screen } from '@testing-library/react';
import { KPICard } from './kpi-card';

describe('KPICard', () => {
  it('renders title and value', () => {
    // Arrange & Act
    render(<KPICard title="Budget" value={100000} unit="USD" />);

    // Assert
    expect(screen.getByText('Budget')).toBeInTheDocument();
    expect(screen.getByText('100,000 USD')).toBeInTheDocument();
  });
});
```

## Documentation

### Docstrings (Python)

```python
def calculate_variance(budget: float, actual: float) -> float:
    """Calculate budget variance.

    Args:
        budget: Planned budget amount.
        actual: Actual spent amount.

    Returns:
        Variance as actual minus budget (negative = under budget).

    Raises:
        ValueError: If budget or actual is negative.
    """
    if budget < 0 or actual < 0:
        raise ValueError("Amounts cannot be negative")
    return actual - budget
```

### JSDoc (TypeScript)

```typescript
/**
 * Calculate budget variance.
 *
 * @param budget - Planned budget amount
 * @param actual - Actual spent amount
 * @returns Variance as actual minus budget (negative = under budget)
 * @throws {Error} If budget or actual is negative
 */
function calculateVariance(budget: number, actual: number): number {
  if (budget < 0 || actual < 0) {
    throw new Error('Amounts cannot be negative');
  }
  return actual - budget;
}
```
