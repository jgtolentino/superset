# Scout Dashboard SQL Views

This directory contains the PostgreSQL views required for the Scout Agency Performance Overview dashboard in Apache Superset.

## Overview

The Scout Dashboard provides comprehensive visibility into TBWA agency campaign performance, media spend, and marketing KPIs across clients, brands, channels, and markets.

## Files

| File | Description |
|------|-------------|
| `V001__create_scout_dashboard_views.sql` | Consolidated migration with all views (recommended) |
| `001_dim_client.sql` | Client dimension view |
| `002_dim_brand.sql` | Brand dimension view |
| `003_dim_campaign.sql` | Campaign dimension view |
| `004_dim_channel.sql` | Media channel dimension view |
| `005_dim_market.sql` | Geographic market dimension view |
| `006_dim_time.sql` | Time/date dimension view |
| `007_bi_fact_campaign_performance.sql` | Core performance fact view |
| `008_bi_campaign_summary.sql` | Campaign-level aggregated summary |
| `deploy_scout_views.sh` | Deployment script |

## Prerequisites

### Environment Variables

```bash
export EXAMPLES_DB_URI="postgresql+psycopg2://user:pass@host:port/database"
```

### Source Tables

The views depend on these source tables from the TBWA Agency Databank:

**Dimension Tables:**
- `clients` - Client organizations
- `brands` - Brand entities (child of clients)
- `campaigns` - Advertising campaigns
- `channels` - Media channels
- `markets` - Geographic markets
- `date_dim` - Calendar/date dimension

**Fact Tables:**
- `campaign_performance` - Daily performance metrics by campaign/channel/market
- `media_spend` - Daily spend data by campaign/channel/market

## Deployment

### Option 1: Consolidated Migration (Recommended)

```bash
./deploy_scout_views.sh
```

Or manually:

```bash
psql "$EXAMPLES_DB_URI" -f V001__create_scout_dashboard_views.sql
```

### Option 2: Individual Files

Execute in order:

```bash
for file in 00*.sql; do
  psql "$EXAMPLES_DB_URI" -f "$file"
done
```

## View Descriptions

### Dimension Views

| View | Grain | Key Columns |
|------|-------|-------------|
| `dim_client` | One row per active client | `client_id`, `client_name`, `industry`, `client_tier` |
| `dim_brand` | One row per active brand | `brand_id`, `brand_name`, `brand_category`, `client_id` |
| `dim_campaign` | One row per campaign | `campaign_id`, `campaign_name`, `brand_id`, `client_id` |
| `dim_channel` | One row per channel | `channel_id`, `channel_name`, `channel_type`, `is_digital` |
| `dim_market` | One row per market | `market_id`, `market_name`, `market_region`, `country` |
| `dim_time` | One row per date | `full_date`, `year`, `quarter`, `month`, `fiscal_year` |

### Fact Views

| View | Grain | Key Metrics |
|------|-------|-------------|
| `bi_fact_campaign_performance` | Campaign × Date × Channel × Market | `impressions`, `clicks`, `reach`, `conversions`, `net_spend`, `ctr`, `cpc`, `cpm`, `cpa` |
| `bi_campaign_summary` | One row per campaign (aggregated) | `total_impressions`, `total_clicks`, `total_net_spend`, `campaign_ctr`, `budget_utilization_pct` |

## Schema Mapping

If source table/column names differ from assumptions, update the SQL views accordingly:

```sql
-- Example: Map assumed table to actual
-- ASSUMED: clients
-- ACTUAL: your_actual_client_table

-- ASSUMED: client_name
-- ACTUAL: your_actual_column_name
```

## Verification

After deployment, verify views exist:

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND (table_name LIKE 'dim_%' OR table_name LIKE 'bi_%')
ORDER BY table_name;
```

Check row counts:

```sql
SELECT 'bi_fact_campaign_performance' AS view_name, COUNT(*) FROM bi_fact_campaign_performance
UNION ALL
SELECT 'bi_campaign_summary', COUNT(*) FROM bi_campaign_summary;
```

## Superset Registration

After deploying views, register as datasets in Superset:

1. Navigate to **Data > Datasets > + Dataset**
2. Select database connection
3. Select schema: `public`
4. Select each view as a table
5. Configure columns and metrics per specification

See [SCOUT_DASHBOARD_SPECIFICATION.md](../docs/SCOUT_DASHBOARD_SPECIFICATION.md) for full dataset configuration.

## Maintenance

### Refresh Views

Views are automatically up-to-date with source data. No manual refresh needed.

### Schema Changes

If source tables change:

1. Update affected view SQL
2. Re-run the migration (idempotent)
3. Verify in Superset that columns/metrics still work

### Performance

For large datasets, consider:

1. Creating materialized views instead of regular views
2. Adding indexes on source tables for join columns
3. Implementing incremental refresh patterns

## Related Documentation

- [Scout Dashboard Specification](../../docs/SCOUT_DASHBOARD_SPECIFICATION.md)
- [Dashboard Import Guide](../../docs/DASHBOARD_IMPORT.md)
- [Superset Deployment](../../docs/README.md)
