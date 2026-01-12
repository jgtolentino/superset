# Scout Dashboard Specification for Apache Superset

**Document Version:** 1.0
**Target Repository:** jgtolentino/tbwa-agency-databank @ v-prod-cutover-1
**Generated:** 2026-01-12
**Target Platform:** Apache Superset with PostgreSQL

---

## ASSUMPTIONS

Since the TBWA Agency Databank repository at tag `v-prod-cutover-1` was not directly accessible during analysis, this specification is based on:

1. **Industry Knowledge**: TBWA is a global advertising agency (Omnicom Group) with standard agency metrics for campaign performance, media spend, and brand management.
2. **Common Agency Data Patterns**: Advertising databanks typically track campaigns, clients, brands, channels, geographies, and performance metrics.
3. **Standard BI Structures**: Fact-dimension star schema patterns common in marketing analytics.
4. **Naming Conventions**: Following common SQL conventions with `bi_`, `dim_`, `fact_`, and `vw_` prefixes.

All table/column names are inferred from typical agency reporting systems and can be mapped to actual schema once repository access is confirmed.

---

## SECTION: REPO_SURVEY

### Expected Directory Structure (Inferred)

```
tbwa-agency-databank/
├── db/
│   ├── migrations/           # SQL DDL migrations (Flyway/Alembic style)
│   │   ├── V001__initial_schema.sql
│   │   ├── V002__add_campaigns.sql
│   │   └── V003__add_performance.sql
│   ├── schema/
│   │   └── databank.dbml     # Database schema definition
│   └── seeds/
│       ├── clients.sql       # Reference data
│       ├── brands.sql
│       └── channels.sql
├── etl/
│   ├── pipelines/
│   │   ├── campaign_ingest.py
│   │   ├── performance_etl.py
│   │   └── spend_aggregation.py
│   └── dbt/                  # dbt transformations (if used)
│       └── models/
│           ├── staging/
│           ├── marts/
│           └── bi/
├── analytics/
│   ├── views/
│   │   ├── bi_campaign_summary.sql
│   │   ├── bi_spend_analysis.sql
│   │   └── mart_performance.sql
│   └── metrics/
│       └── kpi_definitions.yaml
├── docs/
│   ├── data_dictionary.md
│   ├── schema_diagram.png
│   └── metrics_glossary.md
└── config/
    ├── database.yaml
    └── superset_datasets.yaml
```

### Key Components (Inferred Roles)

| Directory/File | Role |
|---------------|------|
| `db/migrations/` | Version-controlled DDL for creating/altering tables |
| `db/schema/*.dbml` | Schema definition in DBML format for documentation |
| `db/seeds/` | Reference data inserts for dimensions |
| `etl/pipelines/` | Python/SQL scripts for data ingestion from source systems |
| `etl/dbt/` | dbt models for transformations (staging → marts → BI) |
| `analytics/views/` | Pre-built SQL views for BI consumption |
| `analytics/metrics/` | KPI definitions and metric configurations |
| `docs/` | Schema documentation and data dictionaries |
| `config/` | Connection and configuration files |

---

## SECTION: DATA_MODEL_RAW

### Fact-Like Tables (Transactional/Event Data)

#### 1. `campaign_performance`
| Attribute | Description |
|-----------|-------------|
| **Name** | `campaign_performance` |
| **Grain** | One row per campaign per day per channel |
| **Primary Key** | `performance_id` (surrogate) or composite (`campaign_id`, `date`, `channel_id`) |
| **Foreign Keys** | `campaign_id`, `channel_id`, `market_id` |
| **Metrics** | `impressions`, `clicks`, `reach`, `frequency`, `engagements`, `conversions`, `video_views`, `video_completions` |

#### 2. `media_spend`
| Attribute | Description |
|-----------|-------------|
| **Name** | `media_spend` |
| **Grain** | One row per campaign per day per channel per market |
| **Primary Key** | `spend_id` (surrogate) or composite |
| **Foreign Keys** | `campaign_id`, `channel_id`, `market_id`, `vendor_id` |
| **Metrics** | `gross_spend`, `net_spend`, `agency_commission`, `production_cost`, `budget_allocated` |

#### 3. `campaign_events`
| Attribute | Description |
|-----------|-------------|
| **Name** | `campaign_events` |
| **Grain** | One row per campaign lifecycle event |
| **Primary Key** | `event_id` |
| **Foreign Keys** | `campaign_id`, `user_id` |
| **Attributes** | `event_type` (created, approved, launched, paused, completed), `event_timestamp`, `notes` |

### Dimension-Like Tables (Reference/Master Data)

#### 1. `clients`
| Attribute | Description |
|-----------|-------------|
| **Name** | `clients` |
| **Grain** | One row per client organization |
| **Primary Key** | `client_id` |
| **Attributes** | `client_name`, `client_code`, `industry`, `region`, `account_director`, `client_since_date`, `tier`, `is_active` |

#### 2. `brands`
| Attribute | Description |
|-----------|-------------|
| **Name** | `brands` |
| **Grain** | One row per brand (sub-unit of client) |
| **Primary Key** | `brand_id` |
| **Foreign Keys** | `client_id` |
| **Attributes** | `brand_name`, `brand_code`, `category`, `sub_category`, `brand_tier`, `is_active` |

#### 3. `campaigns`
| Attribute | Description |
|-----------|-------------|
| **Name** | `campaigns` |
| **Grain** | One row per advertising campaign |
| **Primary Key** | `campaign_id` |
| **Foreign Keys** | `brand_id`, `client_id` |
| **Attributes** | `campaign_name`, `campaign_code`, `campaign_type`, `objective`, `start_date`, `end_date`, `status`, `total_budget`, `creative_theme` |

#### 4. `channels`
| Attribute | Description |
|-----------|-------------|
| **Name** | `channels` |
| **Grain** | One row per media channel |
| **Primary Key** | `channel_id` |
| **Attributes** | `channel_name`, `channel_type` (Digital, TV, Print, OOH, Radio), `sub_channel`, `platform`, `is_digital` |

#### 5. `markets`
| Attribute | Description |
|-----------|-------------|
| **Name** | `markets` |
| **Grain** | One row per geographic market |
| **Primary Key** | `market_id` |
| **Attributes** | `market_name`, `market_code`, `region`, `country`, `timezone`, `currency` |

#### 6. `date_dim`
| Attribute | Description |
|-----------|-------------|
| **Name** | `date_dim` |
| **Grain** | One row per calendar date |
| **Primary Key** | `date_id` or `date_key` |
| **Attributes** | `full_date`, `year`, `quarter`, `month`, `month_name`, `week`, `day_of_week`, `day_name`, `is_weekend`, `is_holiday`, `fiscal_year`, `fiscal_quarter` |

### Relationships Summary

```
clients (1) ──────< (N) brands
brands  (1) ──────< (N) campaigns
campaigns (1) ────< (N) campaign_performance
campaigns (1) ────< (N) media_spend
channels (1) ─────< (N) campaign_performance
channels (1) ─────< (N) media_spend
markets (1) ──────< (N) campaign_performance
markets (1) ──────< (N) media_spend
date_dim (1) ────< (N) campaign_performance (via date)
date_dim (1) ────< (N) media_spend (via date)
```

---

## SECTION: SCOUT_DATA_MODEL

### Facts

#### fact_campaign_performance

| Property | Value |
|----------|-------|
| **id** | `fact_campaign_performance` |
| **source_table** | `campaign_performance` |
| **grain** | Campaign × Date × Channel (daily performance by channel) |
| **key_dimensions** | `campaign_id` → `dim_campaign`, `channel_id` → `dim_channel`, `market_id` → `dim_market`, `date` → `dim_time` |
| **measures** | `impressions` (SUM), `clicks` (SUM), `reach` (SUM), `engagements` (SUM), `conversions` (SUM), `video_views` (SUM), `video_completions` (SUM) |

#### fact_media_spend

| Property | Value |
|----------|-------|
| **id** | `fact_media_spend` |
| **source_table** | `media_spend` |
| **grain** | Campaign × Date × Channel × Market (daily spend by channel/market) |
| **key_dimensions** | `campaign_id` → `dim_campaign`, `channel_id` → `dim_channel`, `market_id` → `dim_market`, `date` → `dim_time` |
| **measures** | `gross_spend` (SUM), `net_spend` (SUM), `agency_commission` (SUM), `budget_allocated` (SUM) |

### Dimensions

#### dim_client

| Property | Value |
|----------|-------|
| **id** | `dim_client` |
| **source_table** | `clients` |
| **business_meaning** | Client organizations served by the agency |
| **key_attributes** | `client_id`, `client_name`, `client_code`, `industry`, `region`, `tier`, `is_active` |

#### dim_brand

| Property | Value |
|----------|-------|
| **id** | `dim_brand` |
| **source_table** | `brands` |
| **business_meaning** | Brand entities managed per client |
| **key_attributes** | `brand_id`, `brand_name`, `brand_code`, `category`, `sub_category`, `client_id` |

#### dim_campaign

| Property | Value |
|----------|-------|
| **id** | `dim_campaign` |
| **source_table** | `campaigns` |
| **business_meaning** | Individual advertising campaigns |
| **key_attributes** | `campaign_id`, `campaign_name`, `campaign_code`, `campaign_type`, `objective`, `status`, `start_date`, `end_date`, `total_budget`, `brand_id`, `client_id` |

#### dim_channel

| Property | Value |
|----------|-------|
| **id** | `dim_channel` |
| **source_table** | `channels` |
| **business_meaning** | Media channels for advertising delivery |
| **key_attributes** | `channel_id`, `channel_name`, `channel_type`, `sub_channel`, `platform`, `is_digital` |

#### dim_market

| Property | Value |
|----------|-------|
| **id** | `dim_market` |
| **source_table** | `markets` |
| **business_meaning** | Geographic markets for campaign targeting |
| **key_attributes** | `market_id`, `market_name`, `market_code`, `region`, `country`, `currency` |

#### dim_time

| Property | Value |
|----------|-------|
| **id** | `dim_time` |
| **source_table** | `date_dim` |
| **business_meaning** | Calendar date dimension for time-series analysis |
| **key_attributes** | `date_key`, `full_date`, `year`, `quarter`, `month`, `month_name`, `week`, `day_of_week`, `fiscal_year`, `fiscal_quarter` |

### Relationships (Star Schema)

```yaml
relationships:
  - from: fact_campaign_performance.campaign_id
    to: dim_campaign.campaign_id
    type: many_to_one

  - from: fact_campaign_performance.channel_id
    to: dim_channel.channel_id
    type: many_to_one

  - from: fact_campaign_performance.market_id
    to: dim_market.market_id
    type: many_to_one

  - from: fact_campaign_performance.date
    to: dim_time.full_date
    type: many_to_one

  - from: fact_media_spend.campaign_id
    to: dim_campaign.campaign_id
    type: many_to_one

  - from: fact_media_spend.channel_id
    to: dim_channel.channel_id
    type: many_to_one

  - from: fact_media_spend.market_id
    to: dim_market.market_id
    type: many_to_one

  - from: fact_media_spend.date
    to: dim_time.full_date
    type: many_to_one

  - from: dim_campaign.brand_id
    to: dim_brand.brand_id
    type: many_to_one

  - from: dim_campaign.client_id
    to: dim_client.client_id
    type: many_to_one

  - from: dim_brand.client_id
    to: dim_client.client_id
    type: many_to_one
```

---

## SECTION: SCOUT_SQL_VIEWS

### 1. dim_client

```sql
-- dim_client: Client dimension for Scout Dashboard
-- Source: clients table from TBWA Agency Databank

CREATE OR REPLACE VIEW public.dim_client AS
SELECT
    c.client_id,
    c.client_name,
    c.client_code,
    c.industry,
    c.region AS client_region,
    c.account_director,
    c.client_since_date,
    c.tier AS client_tier,
    c.is_active AS client_is_active,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, c.client_since_date)) AS years_as_client
FROM clients c
WHERE c.is_active = TRUE;

COMMENT ON VIEW public.dim_client IS 'Client dimension for Scout Dashboard - active clients only';
```

### 2. dim_brand

```sql
-- dim_brand: Brand dimension for Scout Dashboard
-- Source: brands table joined with clients

CREATE OR REPLACE VIEW public.dim_brand AS
SELECT
    b.brand_id,
    b.brand_name,
    b.brand_code,
    b.category AS brand_category,
    b.sub_category AS brand_sub_category,
    b.brand_tier,
    b.is_active AS brand_is_active,
    b.client_id,
    c.client_name,
    c.client_code,
    c.industry AS client_industry
FROM brands b
INNER JOIN clients c ON b.client_id = c.client_id
WHERE b.is_active = TRUE;

COMMENT ON VIEW public.dim_brand IS 'Brand dimension for Scout Dashboard - includes client denormalization';
```

### 3. dim_campaign

```sql
-- dim_campaign: Campaign dimension for Scout Dashboard
-- Source: campaigns table joined with brands and clients

CREATE OR REPLACE VIEW public.dim_campaign AS
SELECT
    ca.campaign_id,
    ca.campaign_name,
    ca.campaign_code,
    ca.campaign_type,
    ca.objective AS campaign_objective,
    ca.start_date AS campaign_start_date,
    ca.end_date AS campaign_end_date,
    ca.status AS campaign_status,
    ca.total_budget AS campaign_budget,
    ca.creative_theme,
    ca.brand_id,
    b.brand_name,
    b.brand_code,
    b.category AS brand_category,
    ca.client_id,
    c.client_name,
    c.client_code,
    c.industry AS client_industry,
    CASE
        WHEN ca.status = 'completed' THEN 'Completed'
        WHEN ca.status = 'active' AND CURRENT_DATE BETWEEN ca.start_date AND ca.end_date THEN 'In Flight'
        WHEN ca.status = 'active' AND CURRENT_DATE < ca.start_date THEN 'Scheduled'
        WHEN ca.status = 'paused' THEN 'Paused'
        ELSE 'Other'
    END AS campaign_status_display,
    (ca.end_date - ca.start_date) AS campaign_duration_days
FROM campaigns ca
INNER JOIN brands b ON ca.brand_id = b.brand_id
INNER JOIN clients c ON ca.client_id = c.client_id;

COMMENT ON VIEW public.dim_campaign IS 'Campaign dimension for Scout Dashboard - includes brand and client denormalization';
```

### 4. dim_channel

```sql
-- dim_channel: Media channel dimension for Scout Dashboard
-- Source: channels table

CREATE OR REPLACE VIEW public.dim_channel AS
SELECT
    ch.channel_id,
    ch.channel_name,
    ch.channel_type,
    ch.sub_channel,
    ch.platform,
    ch.is_digital,
    CASE
        WHEN ch.is_digital = TRUE THEN 'Digital'
        ELSE 'Traditional'
    END AS channel_category,
    CASE ch.channel_type
        WHEN 'Digital' THEN 1
        WHEN 'TV' THEN 2
        WHEN 'OOH' THEN 3
        WHEN 'Print' THEN 4
        WHEN 'Radio' THEN 5
        ELSE 6
    END AS channel_sort_order
FROM channels ch;

COMMENT ON VIEW public.dim_channel IS 'Media channel dimension for Scout Dashboard';
```

### 5. dim_market

```sql
-- dim_market: Geographic market dimension for Scout Dashboard
-- Source: markets table

CREATE OR REPLACE VIEW public.dim_market AS
SELECT
    m.market_id,
    m.market_name,
    m.market_code,
    m.region AS market_region,
    m.country,
    m.timezone AS market_timezone,
    m.currency AS market_currency
FROM markets m;

COMMENT ON VIEW public.dim_market IS 'Geographic market dimension for Scout Dashboard';
```

### 6. dim_time

```sql
-- dim_time: Time/date dimension for Scout Dashboard
-- Source: date_dim table or generated

CREATE OR REPLACE VIEW public.dim_time AS
SELECT
    d.date_key,
    d.full_date,
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    d.week,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    d.is_holiday,
    d.fiscal_year,
    d.fiscal_quarter,
    d.year || '-Q' || d.quarter AS year_quarter,
    d.year || '-' || LPAD(d.month::TEXT, 2, '0') AS year_month,
    d.fiscal_year || '-FQ' || d.fiscal_quarter AS fiscal_year_quarter
FROM date_dim d;

COMMENT ON VIEW public.dim_time IS 'Time dimension for Scout Dashboard - calendar and fiscal periods';
```

### 7. bi_fact_campaign_performance (Main Fact View)

```sql
-- bi_fact_campaign_performance: Core performance fact for Scout Dashboard
-- Combines campaign performance with spend data and all dimension attributes

CREATE OR REPLACE VIEW public.bi_fact_campaign_performance AS
SELECT
    -- Keys
    cp.performance_id,
    cp.campaign_id,
    cp.channel_id,
    cp.market_id,
    cp.date AS performance_date,

    -- Time attributes (denormalized)
    dt.year,
    dt.quarter,
    dt.month,
    dt.month_name,
    dt.week,
    dt.fiscal_year,
    dt.fiscal_quarter,
    dt.year_quarter,
    dt.year_month,

    -- Campaign attributes (denormalized)
    dc.campaign_name,
    dc.campaign_code,
    dc.campaign_type,
    dc.campaign_objective,
    dc.campaign_status,
    dc.campaign_status_display,
    dc.campaign_budget,
    dc.campaign_start_date,
    dc.campaign_end_date,

    -- Brand attributes (denormalized)
    dc.brand_id,
    dc.brand_name,
    dc.brand_code,
    dc.brand_category,

    -- Client attributes (denormalized)
    dc.client_id,
    dc.client_name,
    dc.client_code,
    dc.client_industry,

    -- Channel attributes (denormalized)
    dch.channel_name,
    dch.channel_type,
    dch.sub_channel,
    dch.platform,
    dch.is_digital,
    dch.channel_category,

    -- Market attributes (denormalized)
    dm.market_name,
    dm.market_code,
    dm.market_region,
    dm.country,
    dm.market_currency,

    -- Performance metrics
    COALESCE(cp.impressions, 0) AS impressions,
    COALESCE(cp.clicks, 0) AS clicks,
    COALESCE(cp.reach, 0) AS reach,
    COALESCE(cp.frequency, 0) AS frequency,
    COALESCE(cp.engagements, 0) AS engagements,
    COALESCE(cp.conversions, 0) AS conversions,
    COALESCE(cp.video_views, 0) AS video_views,
    COALESCE(cp.video_completions, 0) AS video_completions,

    -- Spend metrics (joined from media_spend)
    COALESCE(ms.gross_spend, 0) AS gross_spend,
    COALESCE(ms.net_spend, 0) AS net_spend,
    COALESCE(ms.agency_commission, 0) AS agency_commission,
    COALESCE(ms.budget_allocated, 0) AS budget_allocated,

    -- Calculated metrics
    CASE
        WHEN COALESCE(cp.impressions, 0) > 0
        THEN ROUND((COALESCE(cp.clicks, 0)::NUMERIC / cp.impressions) * 100, 4)
        ELSE 0
    END AS ctr,

    CASE
        WHEN COALESCE(cp.clicks, 0) > 0
        THEN ROUND(COALESCE(ms.net_spend, 0)::NUMERIC / cp.clicks, 2)
        ELSE 0
    END AS cpc,

    CASE
        WHEN COALESCE(cp.impressions, 0) > 0
        THEN ROUND((COALESCE(ms.net_spend, 0)::NUMERIC / cp.impressions) * 1000, 2)
        ELSE 0
    END AS cpm,

    CASE
        WHEN COALESCE(cp.conversions, 0) > 0
        THEN ROUND(COALESCE(ms.net_spend, 0)::NUMERIC / cp.conversions, 2)
        ELSE 0
    END AS cpa,

    CASE
        WHEN COALESCE(cp.video_views, 0) > 0
        THEN ROUND((COALESCE(cp.video_completions, 0)::NUMERIC / cp.video_views) * 100, 2)
        ELSE 0
    END AS vcr

FROM campaign_performance cp

-- Join dimensions
INNER JOIN dim_campaign dc ON cp.campaign_id = dc.campaign_id
INNER JOIN dim_channel dch ON cp.channel_id = dch.channel_id
INNER JOIN dim_market dm ON cp.market_id = dm.market_id
INNER JOIN dim_time dt ON cp.date = dt.full_date

-- Join spend data (same grain)
LEFT JOIN media_spend ms
    ON cp.campaign_id = ms.campaign_id
    AND cp.channel_id = ms.channel_id
    AND cp.market_id = ms.market_id
    AND cp.date = ms.date;

COMMENT ON VIEW public.bi_fact_campaign_performance IS 'Main fact view for Scout Dashboard - campaign performance with spend and all dimensions denormalized';
```

### 8. bi_campaign_summary (Aggregated Summary)

```sql
-- bi_campaign_summary: Campaign-level aggregated summary for Scout Dashboard
-- Pre-aggregated metrics at campaign level for high-level reporting

CREATE OR REPLACE VIEW public.bi_campaign_summary AS
SELECT
    dc.campaign_id,
    dc.campaign_name,
    dc.campaign_code,
    dc.campaign_type,
    dc.campaign_objective,
    dc.campaign_status,
    dc.campaign_status_display,
    dc.campaign_budget,
    dc.campaign_start_date,
    dc.campaign_end_date,
    dc.campaign_duration_days,
    dc.brand_id,
    dc.brand_name,
    dc.brand_code,
    dc.brand_category,
    dc.client_id,
    dc.client_name,
    dc.client_code,
    dc.client_industry,

    -- Aggregated metrics
    SUM(COALESCE(cp.impressions, 0)) AS total_impressions,
    SUM(COALESCE(cp.clicks, 0)) AS total_clicks,
    SUM(COALESCE(cp.reach, 0)) AS total_reach,
    SUM(COALESCE(cp.engagements, 0)) AS total_engagements,
    SUM(COALESCE(cp.conversions, 0)) AS total_conversions,
    SUM(COALESCE(cp.video_views, 0)) AS total_video_views,
    SUM(COALESCE(cp.video_completions, 0)) AS total_video_completions,
    SUM(COALESCE(ms.gross_spend, 0)) AS total_gross_spend,
    SUM(COALESCE(ms.net_spend, 0)) AS total_net_spend,
    SUM(COALESCE(ms.budget_allocated, 0)) AS total_budget_allocated,

    -- Calculated rates
    CASE
        WHEN SUM(COALESCE(cp.impressions, 0)) > 0
        THEN ROUND((SUM(COALESCE(cp.clicks, 0))::NUMERIC / SUM(cp.impressions)) * 100, 4)
        ELSE 0
    END AS campaign_ctr,

    CASE
        WHEN SUM(COALESCE(cp.clicks, 0)) > 0
        THEN ROUND(SUM(COALESCE(ms.net_spend, 0))::NUMERIC / SUM(cp.clicks), 2)
        ELSE 0
    END AS campaign_cpc,

    CASE
        WHEN SUM(COALESCE(cp.impressions, 0)) > 0
        THEN ROUND((SUM(COALESCE(ms.net_spend, 0))::NUMERIC / SUM(cp.impressions)) * 1000, 2)
        ELSE 0
    END AS campaign_cpm,

    CASE
        WHEN SUM(COALESCE(cp.conversions, 0)) > 0
        THEN ROUND(SUM(COALESCE(ms.net_spend, 0))::NUMERIC / SUM(cp.conversions), 2)
        ELSE 0
    END AS campaign_cpa,

    -- Budget metrics
    CASE
        WHEN dc.campaign_budget > 0
        THEN ROUND((SUM(COALESCE(ms.net_spend, 0))::NUMERIC / dc.campaign_budget) * 100, 2)
        ELSE 0
    END AS budget_utilization_pct,

    -- Channel mix
    COUNT(DISTINCT cp.channel_id) AS channels_used,
    COUNT(DISTINCT cp.market_id) AS markets_reached,

    -- Date range
    MIN(cp.date) AS first_activity_date,
    MAX(cp.date) AS last_activity_date,
    COUNT(DISTINCT cp.date) AS active_days

FROM dim_campaign dc
LEFT JOIN campaign_performance cp ON dc.campaign_id = cp.campaign_id
LEFT JOIN media_spend ms
    ON cp.campaign_id = ms.campaign_id
    AND cp.channel_id = ms.channel_id
    AND cp.market_id = ms.market_id
    AND cp.date = ms.date

GROUP BY
    dc.campaign_id,
    dc.campaign_name,
    dc.campaign_code,
    dc.campaign_type,
    dc.campaign_objective,
    dc.campaign_status,
    dc.campaign_status_display,
    dc.campaign_budget,
    dc.campaign_start_date,
    dc.campaign_end_date,
    dc.campaign_duration_days,
    dc.brand_id,
    dc.brand_name,
    dc.brand_code,
    dc.brand_category,
    dc.client_id,
    dc.client_name,
    dc.client_code,
    dc.client_industry;

COMMENT ON VIEW public.bi_campaign_summary IS 'Campaign-level aggregated summary for Scout Dashboard - pre-computed totals and rates';
```

---

## SECTION: SUPERSET_DATASETS

```yaml
datasets:
  # Main fact dataset - campaign performance with all dimensions
  - dataset_id: bi_fact_campaign_performance
    table: bi_fact_campaign_performance
    schema: public
    description: "Core Scout dataset combining campaign performance metrics with spend data and all dimension attributes"
    metrics:
      - name: total_impressions
        label: "Total Impressions"
        sql_expression: "SUM(impressions)"
        type: "sum"
        description: "Total number of ad impressions served"

      - name: total_clicks
        label: "Total Clicks"
        sql_expression: "SUM(clicks)"
        type: "sum"
        description: "Total number of clicks on ads"

      - name: total_reach
        label: "Total Reach"
        sql_expression: "SUM(reach)"
        type: "sum"
        description: "Total unique users reached"

      - name: total_engagements
        label: "Total Engagements"
        sql_expression: "SUM(engagements)"
        type: "sum"
        description: "Total engagement actions (likes, shares, comments)"

      - name: total_conversions
        label: "Total Conversions"
        sql_expression: "SUM(conversions)"
        type: "sum"
        description: "Total conversion events"

      - name: total_video_views
        label: "Total Video Views"
        sql_expression: "SUM(video_views)"
        type: "sum"
        description: "Total video view starts"

      - name: total_video_completions
        label: "Total Video Completions"
        sql_expression: "SUM(video_completions)"
        type: "sum"
        description: "Total videos watched to completion"

      - name: total_gross_spend
        label: "Gross Spend"
        sql_expression: "SUM(gross_spend)"
        type: "sum"
        description: "Total gross media spend"

      - name: total_net_spend
        label: "Net Spend"
        sql_expression: "SUM(net_spend)"
        type: "sum"
        description: "Total net media spend (after discounts)"

      - name: avg_ctr
        label: "CTR (%)"
        sql_expression: "CASE WHEN SUM(impressions) > 0 THEN ROUND((SUM(clicks)::NUMERIC / SUM(impressions)) * 100, 4) ELSE 0 END"
        type: "ratio"
        description: "Click-through rate percentage"

      - name: avg_cpc
        label: "CPC ($)"
        sql_expression: "CASE WHEN SUM(clicks) > 0 THEN ROUND(SUM(net_spend)::NUMERIC / SUM(clicks), 2) ELSE 0 END"
        type: "ratio"
        description: "Cost per click"

      - name: avg_cpm
        label: "CPM ($)"
        sql_expression: "CASE WHEN SUM(impressions) > 0 THEN ROUND((SUM(net_spend)::NUMERIC / SUM(impressions)) * 1000, 2) ELSE 0 END"
        type: "ratio"
        description: "Cost per thousand impressions"

      - name: avg_cpa
        label: "CPA ($)"
        sql_expression: "CASE WHEN SUM(conversions) > 0 THEN ROUND(SUM(net_spend)::NUMERIC / SUM(conversions), 2) ELSE 0 END"
        type: "ratio"
        description: "Cost per acquisition/conversion"

      - name: avg_vcr
        label: "VCR (%)"
        sql_expression: "CASE WHEN SUM(video_views) > 0 THEN ROUND((SUM(video_completions)::NUMERIC / SUM(video_views)) * 100, 2) ELSE 0 END"
        type: "ratio"
        description: "Video completion rate percentage"

      - name: campaign_count
        label: "Campaign Count"
        sql_expression: "COUNT(DISTINCT campaign_id)"
        type: "count_distinct"
        description: "Number of unique campaigns"

      - name: active_days
        label: "Active Days"
        sql_expression: "COUNT(DISTINCT performance_date)"
        type: "count_distinct"
        description: "Number of days with activity"

    columns:
      # Primary identifiers
      - name: performance_id
        is_dimension: false
        is_time: false
        verbose_name: "Performance ID"
        description: "Unique row identifier"

      - name: campaign_id
        is_dimension: true
        is_time: false
        verbose_name: "Campaign ID"
        description: "Campaign identifier (FK)"

      - name: channel_id
        is_dimension: true
        is_time: false
        verbose_name: "Channel ID"
        description: "Channel identifier (FK)"

      - name: market_id
        is_dimension: true
        is_time: false
        verbose_name: "Market ID"
        description: "Market identifier (FK)"

      # Time columns
      - name: performance_date
        is_dimension: false
        is_time: true
        verbose_name: "Date"
        description: "Performance date"

      - name: year
        is_dimension: true
        is_time: false
        verbose_name: "Year"
        description: "Calendar year"

      - name: quarter
        is_dimension: true
        is_time: false
        verbose_name: "Quarter"
        description: "Calendar quarter (1-4)"

      - name: month
        is_dimension: true
        is_time: false
        verbose_name: "Month"
        description: "Calendar month (1-12)"

      - name: month_name
        is_dimension: true
        is_time: false
        verbose_name: "Month Name"
        description: "Full month name"

      - name: week
        is_dimension: true
        is_time: false
        verbose_name: "Week"
        description: "Week of year"

      - name: fiscal_year
        is_dimension: true
        is_time: false
        verbose_name: "Fiscal Year"
        description: "Fiscal year"

      - name: fiscal_quarter
        is_dimension: true
        is_time: false
        verbose_name: "Fiscal Quarter"
        description: "Fiscal quarter (1-4)"

      - name: year_quarter
        is_dimension: true
        is_time: false
        verbose_name: "Year-Quarter"
        description: "Combined year-quarter (e.g., 2026-Q1)"

      - name: year_month
        is_dimension: true
        is_time: false
        verbose_name: "Year-Month"
        description: "Combined year-month (e.g., 2026-01)"

      # Campaign dimensions
      - name: campaign_name
        is_dimension: true
        is_time: false
        verbose_name: "Campaign"
        description: "Campaign name"

      - name: campaign_code
        is_dimension: true
        is_time: false
        verbose_name: "Campaign Code"
        description: "Campaign internal code"

      - name: campaign_type
        is_dimension: true
        is_time: false
        verbose_name: "Campaign Type"
        description: "Type of campaign (Brand, Performance, etc.)"

      - name: campaign_objective
        is_dimension: true
        is_time: false
        verbose_name: "Objective"
        description: "Campaign objective"

      - name: campaign_status
        is_dimension: true
        is_time: false
        verbose_name: "Status"
        description: "Campaign status"

      - name: campaign_status_display
        is_dimension: true
        is_time: false
        verbose_name: "Status (Display)"
        description: "Human-readable campaign status"

      # Brand dimensions
      - name: brand_id
        is_dimension: true
        is_time: false
        verbose_name: "Brand ID"
        description: "Brand identifier"

      - name: brand_name
        is_dimension: true
        is_time: false
        verbose_name: "Brand"
        description: "Brand name"

      - name: brand_code
        is_dimension: true
        is_time: false
        verbose_name: "Brand Code"
        description: "Brand internal code"

      - name: brand_category
        is_dimension: true
        is_time: false
        verbose_name: "Brand Category"
        description: "Product category"

      # Client dimensions
      - name: client_id
        is_dimension: true
        is_time: false
        verbose_name: "Client ID"
        description: "Client identifier"

      - name: client_name
        is_dimension: true
        is_time: false
        verbose_name: "Client"
        description: "Client organization name"

      - name: client_code
        is_dimension: true
        is_time: false
        verbose_name: "Client Code"
        description: "Client internal code"

      - name: client_industry
        is_dimension: true
        is_time: false
        verbose_name: "Industry"
        description: "Client industry vertical"

      # Channel dimensions
      - name: channel_name
        is_dimension: true
        is_time: false
        verbose_name: "Channel"
        description: "Media channel name"

      - name: channel_type
        is_dimension: true
        is_time: false
        verbose_name: "Channel Type"
        description: "Channel type (Digital, TV, etc.)"

      - name: sub_channel
        is_dimension: true
        is_time: false
        verbose_name: "Sub-Channel"
        description: "Channel sub-type"

      - name: platform
        is_dimension: true
        is_time: false
        verbose_name: "Platform"
        description: "Platform name (Google, Meta, etc.)"

      - name: is_digital
        is_dimension: true
        is_time: false
        verbose_name: "Is Digital"
        description: "Digital channel flag"

      - name: channel_category
        is_dimension: true
        is_time: false
        verbose_name: "Channel Category"
        description: "Digital vs Traditional"

      # Market dimensions
      - name: market_name
        is_dimension: true
        is_time: false
        verbose_name: "Market"
        description: "Geographic market name"

      - name: market_code
        is_dimension: true
        is_time: false
        verbose_name: "Market Code"
        description: "Market code"

      - name: market_region
        is_dimension: true
        is_time: false
        verbose_name: "Region"
        description: "Geographic region"

      - name: country
        is_dimension: true
        is_time: false
        verbose_name: "Country"
        description: "Country name"

      - name: market_currency
        is_dimension: true
        is_time: false
        verbose_name: "Currency"
        description: "Local currency"

  # Campaign summary dataset - pre-aggregated
  - dataset_id: bi_campaign_summary
    table: bi_campaign_summary
    schema: public
    description: "Pre-aggregated campaign-level summary with computed totals and rates"
    metrics:
      - name: sum_total_impressions
        label: "Total Impressions"
        sql_expression: "SUM(total_impressions)"
        type: "sum"

      - name: sum_total_clicks
        label: "Total Clicks"
        sql_expression: "SUM(total_clicks)"
        type: "sum"

      - name: sum_total_reach
        label: "Total Reach"
        sql_expression: "SUM(total_reach)"
        type: "sum"

      - name: sum_total_conversions
        label: "Total Conversions"
        sql_expression: "SUM(total_conversions)"
        type: "sum"

      - name: sum_net_spend
        label: "Net Spend"
        sql_expression: "SUM(total_net_spend)"
        type: "sum"

      - name: sum_gross_spend
        label: "Gross Spend"
        sql_expression: "SUM(total_gross_spend)"
        type: "sum"

      - name: sum_budget
        label: "Total Budget"
        sql_expression: "SUM(campaign_budget)"
        type: "sum"

      - name: avg_budget_utilization
        label: "Avg Budget Utilization (%)"
        sql_expression: "AVG(budget_utilization_pct)"
        type: "avg"

      - name: count_campaigns
        label: "Campaign Count"
        sql_expression: "COUNT(DISTINCT campaign_id)"
        type: "count_distinct"

      - name: count_brands
        label: "Brand Count"
        sql_expression: "COUNT(DISTINCT brand_id)"
        type: "count_distinct"

      - name: count_clients
        label: "Client Count"
        sql_expression: "COUNT(DISTINCT client_id)"
        type: "count_distinct"

    columns:
      - name: campaign_id
        is_dimension: true
        is_time: false
        verbose_name: "Campaign ID"

      - name: campaign_name
        is_dimension: true
        is_time: false
        verbose_name: "Campaign"

      - name: campaign_type
        is_dimension: true
        is_time: false
        verbose_name: "Campaign Type"

      - name: campaign_objective
        is_dimension: true
        is_time: false
        verbose_name: "Objective"

      - name: campaign_status_display
        is_dimension: true
        is_time: false
        verbose_name: "Status"

      - name: campaign_start_date
        is_dimension: false
        is_time: true
        verbose_name: "Start Date"

      - name: campaign_end_date
        is_dimension: false
        is_time: true
        verbose_name: "End Date"

      - name: brand_name
        is_dimension: true
        is_time: false
        verbose_name: "Brand"

      - name: brand_category
        is_dimension: true
        is_time: false
        verbose_name: "Category"

      - name: client_name
        is_dimension: true
        is_time: false
        verbose_name: "Client"

      - name: client_industry
        is_dimension: true
        is_time: false
        verbose_name: "Industry"

  # Client dimension dataset
  - dataset_id: dim_client
    table: dim_client
    schema: public
    description: "Client master data dimension"
    metrics:
      - name: client_count
        label: "Client Count"
        sql_expression: "COUNT(DISTINCT client_id)"
        type: "count_distinct"
    columns:
      - name: client_id
        is_dimension: true
        is_time: false
        verbose_name: "Client ID"

      - name: client_name
        is_dimension: true
        is_time: false
        verbose_name: "Client"

      - name: industry
        is_dimension: true
        is_time: false
        verbose_name: "Industry"

      - name: client_region
        is_dimension: true
        is_time: false
        verbose_name: "Region"

      - name: client_tier
        is_dimension: true
        is_time: false
        verbose_name: "Tier"

      - name: years_as_client
        is_dimension: true
        is_time: false
        verbose_name: "Years as Client"

  # Brand dimension dataset
  - dataset_id: dim_brand
    table: dim_brand
    schema: public
    description: "Brand master data dimension"
    metrics:
      - name: brand_count
        label: "Brand Count"
        sql_expression: "COUNT(DISTINCT brand_id)"
        type: "count_distinct"
    columns:
      - name: brand_id
        is_dimension: true
        is_time: false
        verbose_name: "Brand ID"

      - name: brand_name
        is_dimension: true
        is_time: false
        verbose_name: "Brand"

      - name: brand_category
        is_dimension: true
        is_time: false
        verbose_name: "Category"

      - name: brand_sub_category
        is_dimension: true
        is_time: false
        verbose_name: "Sub-Category"

      - name: client_name
        is_dimension: true
        is_time: false
        verbose_name: "Client"

  # Channel dimension dataset
  - dataset_id: dim_channel
    table: dim_channel
    schema: public
    description: "Media channel dimension"
    metrics:
      - name: channel_count
        label: "Channel Count"
        sql_expression: "COUNT(DISTINCT channel_id)"
        type: "count_distinct"
    columns:
      - name: channel_id
        is_dimension: true
        is_time: false
        verbose_name: "Channel ID"

      - name: channel_name
        is_dimension: true
        is_time: false
        verbose_name: "Channel"

      - name: channel_type
        is_dimension: true
        is_time: false
        verbose_name: "Type"

      - name: platform
        is_dimension: true
        is_time: false
        verbose_name: "Platform"

      - name: channel_category
        is_dimension: true
        is_time: false
        verbose_name: "Category"

  # Market dimension dataset
  - dataset_id: dim_market
    table: dim_market
    schema: public
    description: "Geographic market dimension"
    metrics:
      - name: market_count
        label: "Market Count"
        sql_expression: "COUNT(DISTINCT market_id)"
        type: "count_distinct"
    columns:
      - name: market_id
        is_dimension: true
        is_time: false
        verbose_name: "Market ID"

      - name: market_name
        is_dimension: true
        is_time: false
        verbose_name: "Market"

      - name: market_region
        is_dimension: true
        is_time: false
        verbose_name: "Region"

      - name: country
        is_dimension: true
        is_time: false
        verbose_name: "Country"
```

---

## SECTION: SCOUT_DASHBOARD_SPEC

```yaml
dashboard:
  id: scout_agency_overview
  title: "Scout - Agency Performance Overview"
  slug: scout-agency-overview
  description: "Executive dashboard providing a comprehensive view of TBWA agency campaign performance, media spend, and key marketing KPIs across clients, brands, channels, and markets."

  primary_datasets:
    - bi_fact_campaign_performance
    - bi_campaign_summary

  css: |
    .scout-kpi-row {
      margin-bottom: 16px;
    }
    .scout-header {
      font-weight: 600;
      color: #1a1a2e;
    }

  native_filters:
    - filter_id: filter_client
      name: "Client"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: client_name
      is_default: true
      multiple: true
      search_all_options: true
      sort_ascending: true
      description: "Filter by client organization"

    - filter_id: filter_brand
      name: "Brand"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: brand_name
      is_default: true
      multiple: true
      search_all_options: true
      parent_filter_ids:
        - filter_client
      description: "Filter by brand (cascading from client)"

    - filter_id: filter_campaign
      name: "Campaign"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: campaign_name
      is_default: true
      multiple: true
      search_all_options: true
      parent_filter_ids:
        - filter_brand
      description: "Filter by campaign (cascading from brand)"

    - filter_id: filter_channel
      name: "Channel"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: channel_name
      is_default: true
      multiple: true
      sort_ascending: true
      description: "Filter by media channel"

    - filter_id: filter_channel_type
      name: "Channel Type"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: channel_type
      is_default: false
      multiple: true
      description: "Filter by channel type (Digital, TV, etc.)"

    - filter_id: filter_market
      name: "Market"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: market_name
      is_default: true
      multiple: true
      sort_ascending: true
      description: "Filter by geographic market"

    - filter_id: filter_region
      name: "Region"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: market_region
      is_default: false
      multiple: true
      description: "Filter by geographic region"

    - filter_id: filter_campaign_status
      name: "Campaign Status"
      filter_type: "filter_select"
      dataset_id: bi_fact_campaign_performance
      column: campaign_status_display
      is_default: false
      multiple: true
      description: "Filter by campaign status"

    - filter_id: filter_date_range
      name: "Date Range"
      filter_type: "filter_time"
      dataset_id: bi_fact_campaign_performance
      column: performance_date
      is_default: true
      time_range: "Last quarter"
      description: "Filter by date range"

  charts:
    # ============================================
    # ROW 1: KPI Cards
    # ============================================
    - key: kpi_total_spend
      title: "Total Net Spend"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 3
      height: 1
      params:
        metric: total_net_spend
        header_font_size: 0.4
        subheader_font_size: 0.15
        y_axis_format: "$,.2f"
        time_grain_sqla: null
        comparisons:
          - comparison_type: values
            enabled: false
      description: "Total net media spend across all filtered campaigns"

    - key: kpi_total_impressions
      title: "Total Impressions"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 3
      height: 1
      params:
        metric: total_impressions
        header_font_size: 0.4
        subheader_font_size: 0.15
        y_axis_format: ",.0f"
      description: "Total impressions delivered"

    - key: kpi_total_reach
      title: "Total Reach"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 3
      height: 1
      params:
        metric: total_reach
        header_font_size: 0.4
        subheader_font_size: 0.15
        y_axis_format: ",.0f"
      description: "Total unique users reached"

    - key: kpi_avg_ctr
      title: "Average CTR"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 3
      height: 1
      params:
        metric: avg_ctr
        header_font_size: 0.4
        subheader_font_size: 0.15
        y_axis_format: ".4%"
      description: "Overall click-through rate"

    # ============================================
    # ROW 2: Secondary KPIs
    # ============================================
    - key: kpi_total_clicks
      title: "Total Clicks"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: total_clicks
        y_axis_format: ",.0f"
      description: "Total clicks generated"

    - key: kpi_total_conversions
      title: "Total Conversions"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: total_conversions
        y_axis_format: ",.0f"
      description: "Total conversions"

    - key: kpi_avg_cpc
      title: "CPC"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: avg_cpc
        y_axis_format: "$,.2f"
      description: "Average cost per click"

    - key: kpi_avg_cpm
      title: "CPM"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: avg_cpm
        y_axis_format: "$,.2f"
      description: "Average cost per thousand impressions"

    - key: kpi_avg_cpa
      title: "CPA"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: avg_cpa
        y_axis_format: "$,.2f"
      description: "Average cost per acquisition"

    - key: kpi_campaign_count
      title: "Campaigns"
      type: "big_number_total"
      dataset_id: bi_fact_campaign_performance
      width: 2
      height: 1
      params:
        metric: campaign_count
        y_axis_format: ",.0f"
      description: "Number of active campaigns"

    # ============================================
    # ROW 3: Time Series Charts
    # ============================================
    - key: chart_spend_over_time
      title: "Net Spend Over Time"
      type: "echarts_timeseries_line"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        x_axis: performance_date
        time_grain_sqla: P1D
        metrics:
          - total_net_spend
        groupby: []
        series_height_on_hover: true
        row_limit: 10000
        truncate_metric: true
        show_legend: true
        legendType: scroll
        legendOrientation: top
        x_axis_time_format: "%Y-%m-%d"
        y_axis_format: "$,.0f"
        rich_tooltip: true
        tooltipTimeFormat: "%Y-%m-%d"
        markerEnabled: false
        markerSize: 6
        zoomable: true
        orientation: vertical
      description: "Daily net spend trend over time"

    - key: chart_impressions_over_time
      title: "Impressions Over Time"
      type: "echarts_timeseries_line"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        x_axis: performance_date
        time_grain_sqla: P1D
        metrics:
          - total_impressions
        groupby: []
        show_legend: true
        legendType: scroll
        legendOrientation: top
        x_axis_time_format: "%Y-%m-%d"
        y_axis_format: ",.0f"
        rich_tooltip: true
        markerEnabled: false
        zoomable: true
      description: "Daily impressions trend over time"

    # ============================================
    # ROW 4: Spend by Channel (Time Series with Breakdown)
    # ============================================
    - key: chart_spend_by_channel_time
      title: "Spend by Channel Over Time"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 12
      height: 2
      params:
        x_axis: performance_date
        time_grain_sqla: P1W
        metrics:
          - total_net_spend
        groupby:
          - channel_name
        show_legend: true
        legendType: scroll
        legendOrientation: top
        stack: true
        x_axis_time_format: "%Y-%m-%d"
        y_axis_format: "$,.0f"
        rich_tooltip: true
        row_limit: 10000
        order_desc: true
      description: "Weekly spend breakdown by channel (stacked)"

    # ============================================
    # ROW 5: Breakdown Charts
    # ============================================
    - key: chart_spend_by_brand
      title: "Spend by Brand"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 4
      height: 2
      params:
        metrics:
          - total_net_spend
        groupby:
          - brand_name
        orientation: horizontal
        show_legend: false
        y_axis_format: "$,.0f"
        row_limit: 15
        order_desc: true
        color_scheme: supersetColors
        bar_stacked: false
      description: "Top brands by net spend"

    - key: chart_spend_by_channel
      title: "Spend by Channel Type"
      type: "pie"
      dataset_id: bi_fact_campaign_performance
      width: 4
      height: 2
      params:
        metric: total_net_spend
        groupby:
          - channel_type
        show_legend: true
        show_labels: true
        label_type: key_percent
        number_format: "$,.0f"
        donut: true
        innerRadius: 40
        outerRadius: 80
        color_scheme: supersetColors
        row_limit: 10
      description: "Spend distribution by channel type"

    - key: chart_spend_by_market
      title: "Spend by Market"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 4
      height: 2
      params:
        metrics:
          - total_net_spend
        groupby:
          - market_name
        orientation: horizontal
        show_legend: false
        y_axis_format: "$,.0f"
        row_limit: 15
        order_desc: true
        color_scheme: supersetColors
      description: "Top markets by net spend"

    # ============================================
    # ROW 6: Performance Comparison Charts
    # ============================================
    - key: chart_ctr_by_channel
      title: "CTR by Channel"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        metrics:
          - avg_ctr
        groupby:
          - channel_name
        orientation: horizontal
        show_legend: false
        y_axis_format: ".4%"
        row_limit: 15
        order_desc: true
        color_scheme: bnbColors
      description: "Click-through rate comparison by channel"

    - key: chart_performance_by_campaign
      title: "Campaign Performance Comparison"
      type: "echarts_timeseries_scatter"
      dataset_id: bi_campaign_summary
      width: 6
      height: 2
      params:
        x: total_net_spend
        y: total_impressions
        size: total_clicks
        entity: campaign_name
        x_axis_format: "$,.0f"
        y_axis_format: ",.0f"
        max_bubble_size: 50
        color_scheme: supersetColors
        row_limit: 100
        show_legend: true
      description: "Campaign scatter plot: Spend vs Impressions (bubble size = clicks)"

    # ============================================
    # ROW 7: Client and Industry Analysis
    # ============================================
    - key: chart_spend_by_client
      title: "Top Clients by Spend"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        metrics:
          - total_net_spend
        groupby:
          - client_name
        orientation: horizontal
        show_legend: false
        y_axis_format: "$,.0f"
        row_limit: 10
        order_desc: true
        color_scheme: supersetColors
      description: "Top 10 clients by net spend"

    - key: chart_spend_by_industry
      title: "Spend by Industry"
      type: "treemap_v2"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        metrics:
          - total_net_spend
        groupby:
          - client_industry
          - client_name
        color_scheme: supersetColors
        show_labels: true
        label_type: key_value
        number_format: "$,.0f"
        row_limit: 100
      description: "Spend distribution by industry and client (treemap)"

    # ============================================
    # ROW 8: Campaign Detail Table
    # ============================================
    - key: table_campaign_details
      title: "Campaign Details"
      type: "table"
      dataset_id: bi_campaign_summary
      width: 12
      height: 3
      params:
        query_mode: raw
        all_columns:
          - campaign_name
          - client_name
          - brand_name
          - campaign_type
          - campaign_status_display
          - campaign_start_date
          - campaign_end_date
          - total_impressions
          - total_clicks
          - total_conversions
          - total_net_spend
          - campaign_ctr
          - campaign_cpc
          - campaign_cpm
          - budget_utilization_pct
        order_by:
          - column: total_net_spend
            order: desc
        page_length: 25
        include_search: true
        table_timestamp_format: "%Y-%m-%d"
        conditional_formatting:
          - column: campaign_ctr
            operator: ">"
            value: 2
            color_scheme: "#d4edda"
          - column: budget_utilization_pct
            operator: ">"
            value: 90
            color_scheme: "#f8d7da"
        column_config:
          total_impressions:
            d3_format: ",.0f"
          total_clicks:
            d3_format: ",.0f"
          total_conversions:
            d3_format: ",.0f"
          total_net_spend:
            d3_format: "$,.2f"
          campaign_ctr:
            d3_format: ".4%"
          campaign_cpc:
            d3_format: "$,.2f"
          campaign_cpm:
            d3_format: "$,.2f"
          budget_utilization_pct:
            d3_format: ".1%"
      description: "Detailed campaign-level table with key metrics and sorting"

    # ============================================
    # ROW 9: Video Performance (if applicable)
    # ============================================
    - key: chart_video_performance
      title: "Video Performance by Campaign"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        metrics:
          - total_video_views
          - total_video_completions
        groupby:
          - campaign_name
        orientation: horizontal
        show_legend: true
        legendType: scroll
        legendOrientation: top
        y_axis_format: ",.0f"
        row_limit: 10
        order_desc: true
        bar_stacked: false
      description: "Video views and completions by campaign"

    - key: chart_vcr_by_channel
      title: "Video Completion Rate by Channel"
      type: "echarts_timeseries_bar"
      dataset_id: bi_fact_campaign_performance
      width: 6
      height: 2
      params:
        metrics:
          - avg_vcr
        groupby:
          - channel_name
        adhoc_filters:
          - clause: "WHERE"
            expressionType: "SQL"
            sqlExpression: "video_views > 0"
        orientation: horizontal
        show_legend: false
        y_axis_format: ".1%"
        row_limit: 15
        order_desc: true
        color_scheme: googleCategory20c
      description: "Video completion rate by channel (filtered to channels with video)"

  layout:
    - row: 1
      title: "Key Performance Indicators"
      charts:
        - kpi_total_spend
        - kpi_total_impressions
        - kpi_total_reach
        - kpi_avg_ctr

    - row: 2
      title: "Secondary Metrics"
      charts:
        - kpi_total_clicks
        - kpi_total_conversions
        - kpi_avg_cpc
        - kpi_avg_cpm
        - kpi_avg_cpa
        - kpi_campaign_count

    - row: 3
      title: "Performance Trends"
      charts:
        - chart_spend_over_time
        - chart_impressions_over_time

    - row: 4
      title: "Channel Spend Analysis"
      charts:
        - chart_spend_by_channel_time

    - row: 5
      title: "Spend Breakdown"
      charts:
        - chart_spend_by_brand
        - chart_spend_by_channel
        - chart_spend_by_market

    - row: 6
      title: "Performance Comparison"
      charts:
        - chart_ctr_by_channel
        - chart_performance_by_campaign

    - row: 7
      title: "Client Analysis"
      charts:
        - chart_spend_by_client
        - chart_spend_by_industry

    - row: 8
      title: "Campaign Details"
      charts:
        - table_campaign_details

    - row: 9
      title: "Video Performance"
      charts:
        - chart_video_performance
        - chart_vcr_by_channel
```

---

## SECTION: IMPLEMENTATION_NOTES

### Step 1: Create Gold Views in the Databank Database

1. **Verify Database Connection**
   ```bash
   # Test PostgreSQL connection
   psql "$EXAMPLES_DB_URI" -c "SELECT 1;"
   ```

2. **Create Dimension Views**
   Execute the following SQL files in order:
   ```bash
   psql "$EXAMPLES_DB_URI" -f sql/dim_client.sql
   psql "$EXAMPLES_DB_URI" -f sql/dim_brand.sql
   psql "$EXAMPLES_DB_URI" -f sql/dim_campaign.sql
   psql "$EXAMPLES_DB_URI" -f sql/dim_channel.sql
   psql "$EXAMPLES_DB_URI" -f sql/dim_market.sql
   psql "$EXAMPLES_DB_URI" -f sql/dim_time.sql
   ```

3. **Create Fact Views**
   ```bash
   psql "$EXAMPLES_DB_URI" -f sql/bi_fact_campaign_performance.sql
   psql "$EXAMPLES_DB_URI" -f sql/bi_campaign_summary.sql
   ```

4. **Verify Views**
   ```sql
   -- Check all views exist
   SELECT table_name, table_type
   FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name LIKE 'dim_%' OR table_name LIKE 'bi_%';

   -- Test row counts
   SELECT 'dim_client' AS view_name, COUNT(*) AS rows FROM dim_client
   UNION ALL
   SELECT 'dim_brand', COUNT(*) FROM dim_brand
   UNION ALL
   SELECT 'bi_fact_campaign_performance', COUNT(*) FROM bi_fact_campaign_performance;
   ```

### Step 2: Register Datasets in Superset

1. **Via Superset UI**
   - Navigate to Data → Datasets → + Dataset
   - Select the database connection to the Databank
   - For each view (`bi_fact_campaign_performance`, `bi_campaign_summary`, `dim_*`):
     - Select schema: `public`
     - Select table: (view name)
     - Save

2. **Configure Dataset Columns**
   - For each dataset, edit and mark columns as:
     - Dimensions (group by): `is_dttm = False`, `filterable = True`, `groupby = True`
     - Time columns: `is_dttm = True` (for date fields)
     - Metrics: Add custom metrics per SUPERSET_DATASETS spec

3. **Via REST API (Automated)**
   ```python
   import requests
   import json

   BASE_URL = os.environ['BASE_URL']

   # Authenticate
   auth_response = requests.post(
       f"{BASE_URL}/api/v1/security/login",
       json={
           "username": os.environ['SUPERSET_ADMIN_USER'],
           "password": os.environ['SUPERSET_ADMIN_PASS'],
           "provider": "db"
       }
   )
   access_token = auth_response.json()['access_token']
   headers = {"Authorization": f"Bearer {access_token}"}

   # Create dataset
   dataset_payload = {
       "database": 1,  # Database ID
       "schema": "public",
       "table_name": "bi_fact_campaign_performance"
   }
   requests.post(f"{BASE_URL}/api/v1/dataset/", headers=headers, json=dataset_payload)
   ```

### Step 3: Build/Import the Scout Dashboard

**Option A: Build via UI**

1. Navigate to Dashboards → + Dashboard
2. Set title: "Scout - Agency Performance Overview"
3. Add charts using the Chart Builder:
   - For each chart in SCOUT_DASHBOARD_SPEC, create using specified type and configuration
   - Assign to appropriate dataset
   - Configure metrics and dimensions
4. Add Native Filters:
   - Click Filter icon → Add filters
   - Add each filter from the spec (Client, Brand, Campaign, etc.)
   - Configure cascading relationships
5. Arrange layout per the layout specification

**Option B: Import via JSON Bundle**

1. Export the dashboard as JSON after building
2. Store in `examples/dashboards/scout_agency_overview.json`
3. Import using the import script:
   ```bash
   ./scripts/import_dashboard.py examples/dashboards/scout_agency_overview.json
   ```

**Option C: Import via REST API**

```bash
# Export dashboard from staging
curl -X GET "${BASE_URL}/api/v1/dashboard/export/?q=[dashboard_id]" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -o scout_dashboard_export.zip

# Import to production
curl -X POST "${BASE_URL}/api/v1/dashboard/import/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -F "formData=@scout_dashboard_export.zip" \
  -F "overwrite=true"
```

### Step 4: Post-Import Configuration

1. **Verify Data Flow**
   ```sql
   -- Check data freshness
   SELECT MAX(performance_date) AS latest_date
   FROM bi_fact_campaign_performance;
   ```

2. **Test Filters**
   - Open dashboard and verify each filter works
   - Test cascading filter relationships (Client → Brand → Campaign)
   - Verify date range filter applies to all charts

3. **Set Refresh Schedule**
   - Dashboard → Settings → Auto Refresh
   - Set appropriate interval (e.g., 5 minutes for near-real-time)

4. **Configure Alerts (Optional)**
   - Alerts & Reports → Create Alert
   - Set threshold conditions for KPIs

### Assumptions Made

Due to repository inaccessibility, the following assumptions were made:

| Assumption | Basis |
|------------|-------|
| **Table Names** | Standard naming conventions for agency databanks (`campaigns`, `clients`, `brands`, `channels`, `markets`, `campaign_performance`, `media_spend`) |
| **Column Names** | Industry-standard field names for advertising metrics |
| **Schema** | PostgreSQL `public` schema |
| **Grain** | Campaign × Date × Channel as the atomic performance grain |
| **Metrics** | Standard digital/traditional advertising KPIs (impressions, clicks, reach, spend, CTR, CPC, CPM, CPA) |
| **Relationships** | Star schema with campaign as the primary fact-to-dimension bridge |
| **Date Dimension** | Pre-populated `date_dim` table with fiscal calendar support |

### Mapping to Actual Schema

Once repository access is confirmed, update the SQL views to map to actual table/column names:

```sql
-- Example mapping template
-- ASSUMPTION: campaigns table
-- ACTUAL: [actual_table_name]

-- ASSUMPTION: campaign_name column
-- ACTUAL: [actual_column_name]
```

### Production Checklist

- [ ] Verify all source tables exist in Databank
- [ ] Map assumed column names to actual schema
- [ ] Execute dimension view creation scripts
- [ ] Execute fact view creation scripts
- [ ] Verify view row counts are non-zero
- [ ] Register all datasets in Superset
- [ ] Configure dataset columns and metrics
- [ ] Create dashboard with all charts
- [ ] Configure native filters with cascading
- [ ] Test all filters and interactivity
- [ ] Set appropriate refresh schedule
- [ ] Configure role-based access if needed
- [ ] Document any schema mapping changes

---

## Appendix: SQL Migration Script

For automated deployment, consolidate all views into a single migration:

```sql
-- V001__create_scout_dashboard_views.sql
-- Scout Dashboard Gold Views for Superset
-- Generated: 2026-01-12

BEGIN;

-- Drop existing views if they exist (for idempotency)
DROP VIEW IF EXISTS public.bi_campaign_summary CASCADE;
DROP VIEW IF EXISTS public.bi_fact_campaign_performance CASCADE;
DROP VIEW IF EXISTS public.dim_time CASCADE;
DROP VIEW IF EXISTS public.dim_market CASCADE;
DROP VIEW IF EXISTS public.dim_channel CASCADE;
DROP VIEW IF EXISTS public.dim_campaign CASCADE;
DROP VIEW IF EXISTS public.dim_brand CASCADE;
DROP VIEW IF EXISTS public.dim_client CASCADE;

-- Create dimension views
-- (Insert full CREATE VIEW statements from SCOUT_SQL_VIEWS section)

-- Create fact views
-- (Insert full CREATE VIEW statements from SCOUT_SQL_VIEWS section)

-- Grant SELECT permissions to Superset service account
GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_readonly;

COMMIT;
```

---

**End of Scout Dashboard Specification**
