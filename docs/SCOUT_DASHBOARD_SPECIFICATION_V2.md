# Scout Dashboard Specification for Apache Superset
# TBWA\SMP Suqi Analytics - Retail Intelligence

**Document Version:** 2.0
**Platform:** TBWA\SMP Suqi Analytics - Retail Intelligence
**Source:** https://scout-dashboard-xi.vercel.app
**Generated:** 2026-01-12
**Target Platform:** Apache Superset with PostgreSQL

---

## OVERVIEW

Scout Dashboard is a retail intelligence platform for TBWA\SMP that analyzes transactions from Philippine sari-sari stores (small neighborhood retail stores). The platform provides insights into:

- Transaction trends and patterns
- Product mix and SKU performance
- Consumer behavior and purchase journeys
- Customer demographics and profiling
- Competitive brand analysis
- Geographic market intelligence

---

## SECTION: DATA_MODEL_RAW

### Core Transaction Table

#### `scout_transactions`

| Field | Type | Required | Description | Example/Values |
|-------|------|----------|-------------|----------------|
| `id` | string | Yes | Unique transaction identifier | `TXN00012847` |
| `store_id` | string | Yes | Store unique identifier (FK to stores) | `ST000284` |
| `timestamp` | ISO 8601 datetime | Yes | UTC datetime of transaction | `2024-06-15T14:32:18.000Z` |
| `time_of_day` | enum | Yes | Period of day | `morning`, `afternoon`, `evening`, `night` |
| `location` | object | Yes | Philippine geographic hierarchy | `{barangay, city, province, region}` |
| `product_category` | string | Yes | High-level product category | `Snack`, `Tobacco`, `Beverages` |
| `brand_name` | string | Yes | Brand of purchased SKU | `Oishi Prawn Crackers` |
| `sku` | string | Yes | Full product SKU/variant | `Oishi Prawn Crackers 30 g` |
| `units_per_transaction` | integer | Yes | Number of units purchased | `2` |
| `peso_value` | float | Yes | Transaction value in PHP | `45.00` |
| `basket_size` | integer | Yes | Number of unique SKUs in transaction | `3` |
| `combo_basket` | array[string] | Yes | List of SKUs in same transaction | `["SKU1", "SKU2"]` |
| `request_mode` | enum | Yes | How product was requested | `verbal`, `pointing`, `indirect` |
| `request_type` | enum | Yes | What customer asked for | `branded`, `unbranded`, `point`, `indirect` |
| `suggestion_accepted` | boolean | Yes | Did customer accept suggestion | `true`, `false` |
| `gender` | enum | Yes | Inferred customer gender | `male`, `female`, `unknown` |
| `age_bracket` | enum | Yes | Estimated age range | `18-24`, `25-34`, `35-44`, `45-54`, `55+`, `unknown` |
| `customer_type` | enum | Yes | Customer relationship | `regular`, `occasional`, `new`, `unknown` |
| `economic_class` | enum | Yes | Socio-economic bracket | `A`, `B`, `C`, `D`, `E`, `unknown` |
| `duration_seconds` | integer | Yes | Transaction duration | `42` |
| `handshake_score` | float | Yes | Engagement quality (0.0-1.0) | `0.85` |
| `payment_method` | enum | Yes | Payment type | `cash`, `gcash`, `maya`, `credit`, `other` |
| `store_type` | enum | Yes | Store typology | `urban_high`, `urban_medium`, `residential`, `rural`, `transport`, `other` |
| `campaign_influenced` | boolean | Yes | Influenced by campaign | `true`, `false` |
| `is_tbwa_client` | boolean | Yes | Is TBWA client brand | `true`, `false` |
| `substitution_event` | object | Yes | Substitution details | `{occurred: bool, from: string, reason: enum}` |

### Dimension Tables (Inferred)

#### `stores`

| Field | Type | Description |
|-------|------|-------------|
| `store_id` | string PK | Store identifier |
| `store_name` | string | Store name |
| `store_type` | enum | Store typology |
| `barangay` | string | Barangay location |
| `city` | string | City |
| `province` | string | Province |
| `region` | string | Region (NCR, CALABARZON, etc.) |
| `latitude` | float | GPS latitude |
| `longitude` | float | GPS longitude |
| `economic_class` | enum | Area economic classification |

#### `products`

| Field | Type | Description |
|-------|------|-------------|
| `sku` | string PK | SKU identifier |
| `brand_name` | string | Brand name |
| `product_category` | string | Category |
| `product_subcategory` | string | Subcategory |
| `is_tbwa_client` | boolean | TBWA client flag |
| `unit_price` | float | Standard unit price |

#### `date_dim`

| Field | Type | Description |
|-------|------|-------------|
| `date_key` | date PK | Date |
| `year` | integer | Year |
| `quarter` | integer | Quarter (1-4) |
| `month` | integer | Month (1-12) |
| `month_name` | string | Month name |
| `week` | integer | Week of year |
| `day_of_week` | integer | Day of week (1-7) |
| `day_name` | string | Day name |
| `is_weekend` | boolean | Weekend flag |

---

## SECTION: SCOUT_DATA_MODEL

### Facts

#### fact_transactions

| Property | Value |
|----------|-------|
| **id** | `fact_transactions` |
| **source_table** | `scout_transactions` |
| **grain** | One row per transaction |
| **key_dimensions** | `store_id` → `dim_store`, `date` → `dim_time`, `sku` → `dim_product` |
| **measures** | `peso_value` (SUM), `units_per_transaction` (SUM), `basket_size` (AVG), `duration_seconds` (AVG), `handshake_score` (AVG), transaction_count (COUNT) |

### Dimensions

| Dimension | Source | Business Meaning |
|-----------|--------|------------------|
| `dim_store` | `stores` | Retail store locations |
| `dim_product` | `products` | SKU/brand catalog |
| `dim_time` | `date_dim` | Calendar dates |
| `dim_customer_segment` | Derived | Customer demographics (age, gender, economic class) |
| `dim_geography` | Derived from location | Philippine regional hierarchy |

---

## SECTION: SCOUT_SQL_VIEWS

### 1. dim_store

```sql
CREATE OR REPLACE VIEW public.dim_store AS
SELECT DISTINCT
    store_id,
    store_type,
    COALESCE(location->>'barangay', 'Unknown') AS barangay,
    COALESCE(location->>'city', 'Unknown') AS city,
    COALESCE(location->>'province', 'Unknown') AS province,
    COALESCE(location->>'region', 'Unknown') AS region,
    economic_class,
    CASE store_type
        WHEN 'urban_high' THEN 'Urban'
        WHEN 'urban_medium' THEN 'Urban'
        WHEN 'residential' THEN 'Suburban'
        WHEN 'rural' THEN 'Rural'
        WHEN 'transport' THEN 'Transit'
        ELSE 'Other'
    END AS store_category
FROM scout_transactions;

COMMENT ON VIEW public.dim_store IS 'Store dimension derived from transaction locations';
```

### 2. dim_product

```sql
CREATE OR REPLACE VIEW public.dim_product AS
SELECT DISTINCT
    sku,
    brand_name,
    product_category,
    is_tbwa_client,
    CASE
        WHEN is_tbwa_client = TRUE THEN 'TBWA Client'
        ELSE 'Competitor'
    END AS brand_type
FROM scout_transactions;

COMMENT ON VIEW public.dim_product IS 'Product/SKU dimension derived from transactions';
```

### 3. dim_time

```sql
CREATE OR REPLACE VIEW public.dim_time AS
SELECT DISTINCT
    DATE(timestamp) AS date_key,
    EXTRACT(YEAR FROM timestamp)::INTEGER AS year,
    EXTRACT(QUARTER FROM timestamp)::INTEGER AS quarter,
    EXTRACT(MONTH FROM timestamp)::INTEGER AS month,
    TO_CHAR(timestamp, 'Month') AS month_name,
    EXTRACT(WEEK FROM timestamp)::INTEGER AS week,
    EXTRACT(DOW FROM timestamp)::INTEGER AS day_of_week,
    TO_CHAR(timestamp, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM timestamp) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    TO_CHAR(timestamp, 'YYYY-Q') AS year_quarter,
    TO_CHAR(timestamp, 'YYYY-MM') AS year_month
FROM scout_transactions;

COMMENT ON VIEW public.dim_time IS 'Time dimension derived from transaction timestamps';
```

### 4. dim_geography

```sql
CREATE OR REPLACE VIEW public.dim_geography AS
SELECT DISTINCT
    COALESCE(location->>'region', 'Unknown') AS region,
    COALESCE(location->>'province', 'Unknown') AS province,
    COALESCE(location->>'city', 'Unknown') AS city,
    COALESCE(location->>'barangay', 'Unknown') AS barangay,
    region || ' > ' || province || ' > ' || city AS geo_hierarchy
FROM scout_transactions
WHERE location IS NOT NULL;

COMMENT ON VIEW public.dim_geography IS 'Philippine geographic hierarchy dimension';
```

### 5. bi_fact_transactions (Main Fact View)

```sql
CREATE OR REPLACE VIEW public.bi_fact_transactions AS
SELECT
    -- Transaction identifiers
    t.id AS transaction_id,
    t.store_id,
    t.timestamp,
    DATE(t.timestamp) AS transaction_date,
    t.time_of_day,

    -- Time dimensions
    EXTRACT(YEAR FROM t.timestamp)::INTEGER AS year,
    EXTRACT(QUARTER FROM t.timestamp)::INTEGER AS quarter,
    EXTRACT(MONTH FROM t.timestamp)::INTEGER AS month,
    TO_CHAR(t.timestamp, 'Month') AS month_name,
    EXTRACT(WEEK FROM t.timestamp)::INTEGER AS week,
    EXTRACT(DOW FROM t.timestamp)::INTEGER AS day_of_week,
    TO_CHAR(t.timestamp, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM t.timestamp) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    EXTRACT(HOUR FROM t.timestamp)::INTEGER AS hour_of_day,

    -- Location dimensions
    COALESCE(t.location->>'region', 'Unknown') AS region,
    COALESCE(t.location->>'province', 'Unknown') AS province,
    COALESCE(t.location->>'city', 'Unknown') AS city,
    COALESCE(t.location->>'barangay', 'Unknown') AS barangay,

    -- Store dimensions
    t.store_type,
    CASE t.store_type
        WHEN 'urban_high' THEN 'Urban'
        WHEN 'urban_medium' THEN 'Urban'
        WHEN 'residential' THEN 'Suburban'
        WHEN 'rural' THEN 'Rural'
        WHEN 'transport' THEN 'Transit'
        ELSE 'Other'
    END AS store_category,

    -- Product dimensions
    t.product_category,
    t.brand_name,
    t.sku,
    t.is_tbwa_client,
    CASE WHEN t.is_tbwa_client THEN 'TBWA Client' ELSE 'Competitor' END AS brand_type,

    -- Customer dimensions
    t.gender,
    t.age_bracket,
    t.customer_type,
    t.economic_class,

    -- Behavior dimensions
    t.request_mode,
    t.request_type,
    t.suggestion_accepted,
    t.payment_method,
    t.campaign_influenced,

    -- Substitution
    COALESCE((t.substitution_event->>'occurred')::BOOLEAN, FALSE) AS substitution_occurred,
    t.substitution_event->>'from' AS substitution_from,
    t.substitution_event->>'reason' AS substitution_reason,

    -- Metrics
    t.units_per_transaction,
    t.peso_value,
    t.basket_size,
    t.duration_seconds,
    t.handshake_score,

    -- Calculated flags
    CASE WHEN t.basket_size >= 3 THEN TRUE ELSE FALSE END AS is_multi_item_basket,
    CASE WHEN t.customer_type = 'regular' THEN TRUE ELSE FALSE END AS is_repeat_customer,
    CASE WHEN t.economic_class IN ('A', 'B') THEN 'High'
         WHEN t.economic_class IN ('C') THEN 'Middle'
         WHEN t.economic_class IN ('D', 'E') THEN 'Low'
         ELSE 'Unknown'
    END AS income_segment

FROM scout_transactions t;

COMMENT ON VIEW public.bi_fact_transactions IS 'Main fact view for Scout Dashboard - retail transactions with all dimensions';
```

### 6. bi_transaction_summary_daily

```sql
CREATE OR REPLACE VIEW public.bi_transaction_summary_daily AS
SELECT
    DATE(timestamp) AS transaction_date,
    COALESCE(location->>'region', 'Unknown') AS region,
    store_type,
    product_category,

    -- Volume metrics
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT id) AS unique_transactions,
    COUNT(DISTINCT store_id) AS active_stores,

    -- Revenue metrics
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,

    -- Basket metrics
    SUM(units_per_transaction) AS total_units,
    AVG(basket_size) AS avg_basket_size,
    SUM(CASE WHEN basket_size >= 3 THEN 1 ELSE 0 END) AS multi_item_baskets,

    -- Duration metrics
    AVG(duration_seconds) AS avg_duration,
    AVG(handshake_score) AS avg_handshake_score,

    -- Customer metrics
    COUNT(DISTINCT CASE WHEN gender = 'male' THEN id END) AS male_customers,
    COUNT(DISTINCT CASE WHEN gender = 'female' THEN id END) AS female_customers,
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN id END) AS repeat_customers,
    COUNT(DISTINCT CASE WHEN customer_type = 'new' THEN id END) AS new_customers,

    -- Behavior metrics
    SUM(CASE WHEN suggestion_accepted THEN 1 ELSE 0 END) AS suggestions_accepted,
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END) AS branded_requests,
    SUM(CASE WHEN campaign_influenced THEN 1 ELSE 0 END) AS campaign_influenced_count,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN THEN 1 ELSE 0 END) AS substitution_count,

    -- TBWA metrics
    SUM(CASE WHEN is_tbwa_client THEN peso_value ELSE 0 END) AS tbwa_revenue,
    COUNT(CASE WHEN is_tbwa_client THEN 1 END) AS tbwa_transactions

FROM scout_transactions
GROUP BY
    DATE(timestamp),
    COALESCE(location->>'region', 'Unknown'),
    store_type,
    product_category;

COMMENT ON VIEW public.bi_transaction_summary_daily IS 'Daily aggregated transaction summary for Scout Dashboard';
```

### 7. bi_product_performance

```sql
CREATE OR REPLACE VIEW public.bi_product_performance AS
SELECT
    brand_name,
    product_category,
    sku,
    is_tbwa_client,
    CASE WHEN is_tbwa_client THEN 'TBWA Client' ELSE 'Competitor' END AS brand_type,

    -- Volume metrics
    COUNT(*) AS transaction_count,
    SUM(units_per_transaction) AS total_units_sold,
    COUNT(DISTINCT store_id) AS stores_carrying,
    COUNT(DISTINCT DATE(timestamp)) AS active_days,

    -- Revenue metrics
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,

    -- Customer metrics
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN id END) AS repeat_buyers,

    -- Behavior metrics
    AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100 AS suggestion_acceptance_rate,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN AND substitution_event->>'from' = brand_name THEN 1 ELSE 0 END) AS substituted_away,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN AND brand_name != substitution_event->>'from' THEN 1 ELSE 0 END) AS substituted_to,

    -- Request patterns
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS branded_request_pct,

    -- Time range
    MIN(timestamp) AS first_sale,
    MAX(timestamp) AS last_sale

FROM scout_transactions
GROUP BY brand_name, product_category, sku, is_tbwa_client;

COMMENT ON VIEW public.bi_product_performance IS 'Product/SKU performance metrics for Scout Dashboard';
```

### 8. bi_customer_segments

```sql
CREATE OR REPLACE VIEW public.bi_customer_segments AS
SELECT
    gender,
    age_bracket,
    economic_class,
    customer_type,
    CASE economic_class
        WHEN 'A' THEN 'High'
        WHEN 'B' THEN 'High'
        WHEN 'C' THEN 'Middle'
        WHEN 'D' THEN 'Low'
        WHEN 'E' THEN 'Low'
        ELSE 'Unknown'
    END AS income_segment,

    -- Volume
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT store_id) AS stores_visited,

    -- Spend
    SUM(peso_value) AS total_spend,
    AVG(peso_value) AS avg_transaction_value,
    AVG(basket_size) AS avg_basket_size,

    -- Behavior
    AVG(duration_seconds) AS avg_duration,
    AVG(handshake_score) AS avg_engagement,
    AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100 AS suggestion_acceptance_rate,

    -- Request patterns
    SUM(CASE WHEN request_mode = 'verbal' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS verbal_request_pct,
    SUM(CASE WHEN request_mode = 'pointing' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS pointing_request_pct,
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS branded_request_pct,

    -- Payment
    SUM(CASE WHEN payment_method = 'cash' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS cash_payment_pct,
    SUM(CASE WHEN payment_method IN ('gcash', 'maya') THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 AS digital_payment_pct,

    -- Category preferences
    MODE() WITHIN GROUP (ORDER BY product_category) AS top_category

FROM scout_transactions
GROUP BY gender, age_bracket, economic_class, customer_type;

COMMENT ON VIEW public.bi_customer_segments IS 'Customer segment analysis for Scout Dashboard';
```

### 9. bi_store_performance

```sql
CREATE OR REPLACE VIEW public.bi_store_performance AS
SELECT
    store_id,
    store_type,
    COALESCE(location->>'region', 'Unknown') AS region,
    COALESCE(location->>'province', 'Unknown') AS province,
    COALESCE(location->>'city', 'Unknown') AS city,
    economic_class,

    -- Volume
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT DATE(timestamp)) AS active_days,
    COUNT(*)::FLOAT / NULLIF(COUNT(DISTINCT DATE(timestamp)), 0) AS avg_daily_transactions,

    -- Revenue
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,
    SUM(peso_value) / NULLIF(COUNT(DISTINCT DATE(timestamp)), 0) AS avg_daily_revenue,

    -- Product mix
    COUNT(DISTINCT sku) AS unique_skus,
    COUNT(DISTINCT brand_name) AS unique_brands,
    COUNT(DISTINCT product_category) AS category_count,

    -- Customer mix
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN gender || age_bracket END) AS repeat_customers,
    AVG(CASE WHEN customer_type = 'regular' THEN 1.0 ELSE 0.0 END) * 100 AS repeat_customer_pct,

    -- Performance
    AVG(handshake_score) AS avg_handshake_score,
    AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100 AS suggestion_acceptance_rate,
    AVG(duration_seconds) AS avg_duration,

    -- TBWA share
    SUM(CASE WHEN is_tbwa_client THEN peso_value ELSE 0 END)::FLOAT /
        NULLIF(SUM(peso_value), 0) * 100 AS tbwa_revenue_share,

    -- Time range
    MIN(timestamp) AS first_transaction,
    MAX(timestamp) AS last_transaction

FROM scout_transactions
GROUP BY
    store_id,
    store_type,
    COALESCE(location->>'region', 'Unknown'),
    COALESCE(location->>'province', 'Unknown'),
    COALESCE(location->>'city', 'Unknown'),
    economic_class;

COMMENT ON VIEW public.bi_store_performance IS 'Store-level performance metrics for Scout Dashboard';
```

### 10. bi_competitive_analysis

```sql
CREATE OR REPLACE VIEW public.bi_competitive_analysis AS
SELECT
    product_category,
    brand_name,
    is_tbwa_client,
    CASE WHEN is_tbwa_client THEN 'TBWA Client' ELSE 'Competitor' END AS brand_type,

    -- Market share metrics
    COUNT(*) AS transaction_count,
    SUM(peso_value) AS total_revenue,
    SUM(units_per_transaction) AS total_units,

    -- Store presence
    COUNT(DISTINCT store_id) AS store_count,

    -- Customer metrics
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN gender || age_bracket END) AS loyal_customers,

    -- Substitution dynamics
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND substitution_event->>'from' = brand_name THEN 1 ELSE 0 END) AS lost_to_substitution,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND brand_name != COALESCE(substitution_event->>'from', '') THEN 1 ELSE 0 END) AS gained_from_substitution,

    -- Request type (brand strength indicator)
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS brand_recall_pct

FROM scout_transactions
GROUP BY product_category, brand_name, is_tbwa_client;

COMMENT ON VIEW public.bi_competitive_analysis IS 'Brand competitive analysis for Scout Dashboard';
```

---

## SECTION: SUPERSET_DATASETS

```yaml
datasets:
  # Main transaction fact
  - dataset_id: bi_fact_transactions
    table: bi_fact_transactions
    schema: public
    description: "Core Scout dataset - individual retail transactions with all dimensions"

    metrics:
      - name: transaction_count
        label: "Transaction Count"
        sql_expression: "COUNT(*)"
        type: "count"

      - name: total_revenue
        label: "Total Revenue (₱)"
        sql_expression: "SUM(peso_value)"
        type: "sum"

      - name: total_units
        label: "Total Units"
        sql_expression: "SUM(units_per_transaction)"
        type: "sum"

      - name: avg_transaction_value
        label: "Avg Transaction Value (₱)"
        sql_expression: "AVG(peso_value)"
        type: "avg"

      - name: avg_basket_size
        label: "Avg Basket Size"
        sql_expression: "AVG(basket_size)"
        type: "avg"

      - name: avg_duration
        label: "Avg Duration (sec)"
        sql_expression: "AVG(duration_seconds)"
        type: "avg"

      - name: avg_handshake_score
        label: "Avg Engagement Score"
        sql_expression: "AVG(handshake_score)"
        type: "avg"

      - name: suggestion_acceptance_rate
        label: "Suggestion Accept Rate (%)"
        sql_expression: "AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100"
        type: "ratio"

      - name: conversion_rate
        label: "Conversion Rate (%)"
        sql_expression: "COUNT(CASE WHEN suggestion_accepted THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
        type: "ratio"

      - name: brand_loyalty_rate
        label: "Brand Loyalty (%)"
        sql_expression: "COUNT(CASE WHEN request_type = 'branded' THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
        type: "ratio"

      - name: tbwa_market_share
        label: "TBWA Market Share (%)"
        sql_expression: "SUM(CASE WHEN is_tbwa_client THEN peso_value ELSE 0 END)::FLOAT / NULLIF(SUM(peso_value), 0) * 100"
        type: "ratio"

      - name: unique_stores
        label: "Active Stores"
        sql_expression: "COUNT(DISTINCT store_id)"
        type: "count_distinct"

      - name: unique_skus
        label: "Active SKUs"
        sql_expression: "COUNT(DISTINCT sku)"
        type: "count_distinct"

      - name: unique_brands
        label: "Active Brands"
        sql_expression: "COUNT(DISTINCT brand_name)"
        type: "count_distinct"

      - name: male_customers
        label: "Male Customers"
        sql_expression: "COUNT(CASE WHEN gender = 'male' THEN 1 END)"
        type: "count"

      - name: female_customers
        label: "Female Customers"
        sql_expression: "COUNT(CASE WHEN gender = 'female' THEN 1 END)"
        type: "count"

      - name: urban_customers
        label: "Urban Customers (%)"
        sql_expression: "COUNT(CASE WHEN store_category = 'Urban' THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
        type: "ratio"

      - name: digital_payment_rate
        label: "Digital Payment Rate (%)"
        sql_expression: "COUNT(CASE WHEN payment_method IN ('gcash', 'maya') THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
        type: "ratio"

      - name: substitution_rate
        label: "Substitution Rate (%)"
        sql_expression: "COUNT(CASE WHEN substitution_occurred THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
        type: "ratio"

    columns:
      # Time dimensions
      - name: transaction_date
        verbose_name: "Date"
        is_dimension: false
        is_time: true

      - name: timestamp
        verbose_name: "Timestamp"
        is_dimension: false
        is_time: true

      - name: time_of_day
        verbose_name: "Time of Day"
        is_dimension: true
        is_time: false

      - name: year
        verbose_name: "Year"
        is_dimension: true
        is_time: false

      - name: quarter
        verbose_name: "Quarter"
        is_dimension: true
        is_time: false

      - name: month
        verbose_name: "Month"
        is_dimension: true
        is_time: false

      - name: month_name
        verbose_name: "Month Name"
        is_dimension: true
        is_time: false

      - name: week
        verbose_name: "Week"
        is_dimension: true
        is_time: false

      - name: day_of_week
        verbose_name: "Day of Week"
        is_dimension: true
        is_time: false

      - name: day_name
        verbose_name: "Day Name"
        is_dimension: true
        is_time: false

      - name: is_weekend
        verbose_name: "Is Weekend"
        is_dimension: true
        is_time: false

      - name: hour_of_day
        verbose_name: "Hour"
        is_dimension: true
        is_time: false

      # Geography dimensions
      - name: region
        verbose_name: "Region"
        is_dimension: true
        is_time: false

      - name: province
        verbose_name: "Province"
        is_dimension: true
        is_time: false

      - name: city
        verbose_name: "City"
        is_dimension: true
        is_time: false

      - name: barangay
        verbose_name: "Barangay"
        is_dimension: true
        is_time: false

      # Store dimensions
      - name: store_id
        verbose_name: "Store ID"
        is_dimension: true
        is_time: false

      - name: store_type
        verbose_name: "Store Type"
        is_dimension: true
        is_time: false

      - name: store_category
        verbose_name: "Store Category"
        is_dimension: true
        is_time: false

      # Product dimensions
      - name: product_category
        verbose_name: "Category"
        is_dimension: true
        is_time: false

      - name: brand_name
        verbose_name: "Brand"
        is_dimension: true
        is_time: false

      - name: sku
        verbose_name: "SKU"
        is_dimension: true
        is_time: false

      - name: is_tbwa_client
        verbose_name: "Is TBWA Client"
        is_dimension: true
        is_time: false

      - name: brand_type
        verbose_name: "Brand Type"
        is_dimension: true
        is_time: false

      # Customer dimensions
      - name: gender
        verbose_name: "Gender"
        is_dimension: true
        is_time: false

      - name: age_bracket
        verbose_name: "Age Bracket"
        is_dimension: true
        is_time: false

      - name: customer_type
        verbose_name: "Customer Type"
        is_dimension: true
        is_time: false

      - name: economic_class
        verbose_name: "Economic Class"
        is_dimension: true
        is_time: false

      - name: income_segment
        verbose_name: "Income Segment"
        is_dimension: true
        is_time: false

      # Behavior dimensions
      - name: request_mode
        verbose_name: "Request Mode"
        is_dimension: true
        is_time: false

      - name: request_type
        verbose_name: "Request Type"
        is_dimension: true
        is_time: false

      - name: suggestion_accepted
        verbose_name: "Suggestion Accepted"
        is_dimension: true
        is_time: false

      - name: payment_method
        verbose_name: "Payment Method"
        is_dimension: true
        is_time: false

      - name: campaign_influenced
        verbose_name: "Campaign Influenced"
        is_dimension: true
        is_time: false

      - name: substitution_occurred
        verbose_name: "Substitution Occurred"
        is_dimension: true
        is_time: false

  # Daily summary
  - dataset_id: bi_transaction_summary_daily
    table: bi_transaction_summary_daily
    schema: public
    description: "Daily aggregated transaction summary"

    metrics:
      - name: sum_transactions
        label: "Total Transactions"
        sql_expression: "SUM(transaction_count)"
        type: "sum"

      - name: sum_revenue
        label: "Total Revenue"
        sql_expression: "SUM(total_revenue)"
        type: "sum"

      - name: avg_revenue_per_store
        label: "Avg Revenue per Store"
        sql_expression: "SUM(total_revenue) / NULLIF(SUM(active_stores), 0)"
        type: "ratio"

    columns:
      - name: transaction_date
        verbose_name: "Date"
        is_dimension: false
        is_time: true

      - name: region
        verbose_name: "Region"
        is_dimension: true
        is_time: false

      - name: store_type
        verbose_name: "Store Type"
        is_dimension: true
        is_time: false

      - name: product_category
        verbose_name: "Category"
        is_dimension: true
        is_time: false

  # Product performance
  - dataset_id: bi_product_performance
    table: bi_product_performance
    schema: public
    description: "Product and SKU performance metrics"

    metrics:
      - name: sum_revenue
        label: "Total Revenue"
        sql_expression: "SUM(total_revenue)"
        type: "sum"

      - name: sum_units
        label: "Total Units"
        sql_expression: "SUM(total_units_sold)"
        type: "sum"

      - name: sum_transactions
        label: "Total Transactions"
        sql_expression: "SUM(transaction_count)"
        type: "sum"

    columns:
      - name: brand_name
        verbose_name: "Brand"
        is_dimension: true
        is_time: false

      - name: product_category
        verbose_name: "Category"
        is_dimension: true
        is_time: false

      - name: sku
        verbose_name: "SKU"
        is_dimension: true
        is_time: false

      - name: brand_type
        verbose_name: "Brand Type"
        is_dimension: true
        is_time: false

  # Customer segments
  - dataset_id: bi_customer_segments
    table: bi_customer_segments
    schema: public
    description: "Customer segment analysis"

    metrics:
      - name: sum_transactions
        label: "Total Transactions"
        sql_expression: "SUM(transaction_count)"
        type: "sum"

      - name: sum_spend
        label: "Total Spend"
        sql_expression: "SUM(total_spend)"
        type: "sum"

    columns:
      - name: gender
        verbose_name: "Gender"
        is_dimension: true
        is_time: false

      - name: age_bracket
        verbose_name: "Age Bracket"
        is_dimension: true
        is_time: false

      - name: economic_class
        verbose_name: "Economic Class"
        is_dimension: true
        is_time: false

      - name: income_segment
        verbose_name: "Income Segment"
        is_dimension: true
        is_time: false

      - name: customer_type
        verbose_name: "Customer Type"
        is_dimension: true
        is_time: false

  # Store performance
  - dataset_id: bi_store_performance
    table: bi_store_performance
    schema: public
    description: "Store-level performance metrics"

    metrics:
      - name: sum_revenue
        label: "Total Revenue"
        sql_expression: "SUM(total_revenue)"
        type: "sum"

      - name: sum_transactions
        label: "Total Transactions"
        sql_expression: "SUM(transaction_count)"
        type: "sum"

      - name: store_count
        label: "Store Count"
        sql_expression: "COUNT(DISTINCT store_id)"
        type: "count_distinct"

    columns:
      - name: store_id
        verbose_name: "Store ID"
        is_dimension: true
        is_time: false

      - name: store_type
        verbose_name: "Store Type"
        is_dimension: true
        is_time: false

      - name: region
        verbose_name: "Region"
        is_dimension: true
        is_time: false

      - name: province
        verbose_name: "Province"
        is_dimension: true
        is_time: false

      - name: city
        verbose_name: "City"
        is_dimension: true
        is_time: false

  # Competitive analysis
  - dataset_id: bi_competitive_analysis
    table: bi_competitive_analysis
    schema: public
    description: "Brand competitive analysis"

    metrics:
      - name: sum_revenue
        label: "Total Revenue"
        sql_expression: "SUM(total_revenue)"
        type: "sum"

      - name: sum_transactions
        label: "Total Transactions"
        sql_expression: "SUM(transaction_count)"
        type: "sum"

      - name: market_share
        label: "Market Share (%)"
        sql_expression: "SUM(total_revenue)::FLOAT / NULLIF(SUM(SUM(total_revenue)) OVER (), 0) * 100"
        type: "ratio"

    columns:
      - name: brand_name
        verbose_name: "Brand"
        is_dimension: true
        is_time: false

      - name: product_category
        verbose_name: "Category"
        is_dimension: true
        is_time: false

      - name: brand_type
        verbose_name: "Brand Type"
        is_dimension: true
        is_time: false
```

---

## SECTION: SCOUT_DASHBOARD_SPEC

```yaml
dashboard:
  id: scout_retail_intelligence
  title: "Scout - Retail Intelligence Dashboard"
  slug: scout-retail-intelligence
  description: "TBWA\\SMP Suqi Analytics platform for Philippine retail (sari-sari store) transaction intelligence, consumer behavior analysis, and competitive insights."

  primary_datasets:
    - bi_fact_transactions
    - bi_transaction_summary_daily
    - bi_product_performance
    - bi_customer_segments
    - bi_store_performance
    - bi_competitive_analysis

  # ========================================
  # NATIVE FILTERS
  # ========================================
  native_filters:
    - filter_id: filter_date_range
      name: "Date Range"
      filter_type: "filter_time"
      dataset_id: bi_fact_transactions
      column: transaction_date
      is_default: true
      time_range: "Last 30 days"

    - filter_id: filter_region
      name: "Region"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: region
      multiple: true
      search_all_options: true

    - filter_id: filter_city
      name: "City"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: city
      multiple: true
      parent_filter_ids: [filter_region]

    - filter_id: filter_store_type
      name: "Store Type"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: store_type
      multiple: true

    - filter_id: filter_category
      name: "Product Category"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: product_category
      multiple: true

    - filter_id: filter_brand
      name: "Brand"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: brand_name
      multiple: true
      parent_filter_ids: [filter_category]

    - filter_id: filter_brand_type
      name: "Brand Type"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: brand_type
      multiple: true

    - filter_id: filter_gender
      name: "Gender"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: gender
      multiple: true

    - filter_id: filter_age_bracket
      name: "Age Bracket"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: age_bracket
      multiple: true

    - filter_id: filter_economic_class
      name: "Economic Class"
      filter_type: "filter_select"
      dataset_id: bi_fact_transactions
      column: economic_class
      multiple: true

  # ========================================
  # TAB 1: TRANSACTION TRENDS
  # ========================================
  tabs:
    - tab_id: transaction_trends
      title: "Transaction Trends"
      subtitle: "Volume, timing & patterns with advanced analytics"

      charts:
        # KPI Row
        - key: kpi_daily_volume
          title: "Daily Volume"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: transaction_count
            y_axis_format: ",.0f"
            subheader: "transactions"
            comparison_color_enabled: true

        - key: kpi_daily_revenue
          title: "Daily Revenue"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: total_revenue
            y_axis_format: "₱,.0f"

        - key: kpi_avg_basket
          title: "Avg Basket Size"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: avg_basket_size
            y_axis_format: ",.1f"

        - key: kpi_avg_duration
          title: "Avg Duration"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: avg_duration
            y_axis_format: ",.0f"
            subheader: "seconds"

        # Time series
        - key: chart_volume_trend
          title: "Transaction Volume Trends"
          type: "echarts_timeseries_line"
          dataset_id: bi_fact_transactions
          width: 12
          height: 3
          params:
            x_axis: transaction_date
            time_grain_sqla: P1D
            metrics: [transaction_count]
            show_legend: false
            y_axis_format: ",.0f"
            rich_tooltip: true
            area: true
            opacity: 0.3
            color_scheme: supersetColors

        # Volume by time of day
        - key: chart_volume_by_time
          title: "Volume by Time of Day"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [transaction_count]
            groupby: [time_of_day]
            y_axis_format: ",.0f"

        # Volume by day of week
        - key: chart_volume_by_dow
          title: "Volume by Day of Week"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [transaction_count]
            groupby: [day_name]
            y_axis_format: ",.0f"

    # ========================================
    # TAB 2: PRODUCT MIX & SKU
    # ========================================
    - tab_id: product_mix
      title: "Product Mix & SKU"
      subtitle: "Category performance, brand insights & cross-sell analysis"

      charts:
        # KPI Row
        - key: kpi_total_skus
          title: "Total SKUs"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: unique_skus
            y_axis_format: ",.0f"

        - key: kpi_active_skus
          title: "Active SKUs"
          type: "big_number_total"
          dataset_id: bi_product_performance
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "COUNT(DISTINCT sku)"
            y_axis_format: ",.0f"

        - key: kpi_unique_brands
          title: "Active Brands"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: unique_brands
            y_axis_format: ",.0f"

        - key: kpi_category_diversity
          title: "Category Diversity"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "COUNT(DISTINCT product_category)"
            y_axis_format: ",.0f"

        # Category distribution
        - key: chart_category_distribution
          title: "Product Category Distribution"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 6
          height: 3
          params:
            metric: total_revenue
            groupby: [product_category]
            donut: true
            show_labels: true
            label_type: key_percent
            number_format: "₱,.0f"

        # Top brands by revenue
        - key: chart_top_brands
          title: "Top Brands by Revenue"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 3
          params:
            metrics: [total_revenue]
            groupby: [brand_name]
            orientation: horizontal
            y_axis_format: "₱,.0f"
            row_limit: 15
            order_desc: true

        # TBWA vs Competitor
        - key: chart_tbwa_vs_competitor
          title: "TBWA Client vs Competitor Revenue"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metric: total_revenue
            groupby: [brand_type]
            donut: true
            show_labels: true
            number_format: "₱,.0f"

        # Substitution analysis
        - key: chart_substitution
          title: "Brand Substitution Analysis"
          type: "echarts_timeseries_bar"
          dataset_id: bi_competitive_analysis
          width: 6
          height: 2
          params:
            metrics:
              - name: lost_to_substitution
                label: "Lost"
              - name: gained_from_substitution
                label: "Gained"
            groupby: [brand_name]
            row_limit: 10

    # ========================================
    # TAB 3: CONSUMER BEHAVIOR
    # ========================================
    - tab_id: consumer_behavior
      title: "Consumer Behavior"
      subtitle: "Purchase decisions, patterns & customer journey analysis"

      charts:
        # KPI Row
        - key: kpi_conversion_rate
          title: "Conversion Rate"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: conversion_rate
            y_axis_format: ".1%"

        - key: kpi_suggestion_accept
          title: "Suggestion Accept"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: suggestion_acceptance_rate
            y_axis_format: ".1%"

        - key: kpi_brand_loyalty
          title: "Brand Loyalty"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: brand_loyalty_rate
            y_axis_format: ".1%"

        - key: kpi_discovery_rate
          title: "Discovery Rate"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "COUNT(CASE WHEN request_type = 'indirect' THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100"
            y_axis_format: ".1%"

        # Request methods distribution
        - key: chart_request_methods
          title: "Request Methods Distribution"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metric: transaction_count
            groupby: [request_mode]
            donut: true
            show_labels: true

        # Request type distribution
        - key: chart_request_type
          title: "Request Type Distribution"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metric: transaction_count
            groupby: [request_type]
            donut: true
            show_labels: true

        # Payment methods
        - key: chart_payment_methods
          title: "Payment Methods"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metric: transaction_count
            groupby: [payment_method]
            donut: true
            show_labels: true

        # Suggestion acceptance by segment
        - key: chart_suggestion_by_segment
          title: "Suggestion Acceptance by Customer Type"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [suggestion_acceptance_rate]
            groupby: [customer_type]
            y_axis_format: ".1%"

        # Brand loyalty by age
        - key: chart_loyalty_by_age
          title: "Brand Loyalty by Age Bracket"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [brand_loyalty_rate]
            groupby: [age_bracket]
            y_axis_format: ".1%"

    # ========================================
    # TAB 4: CONSUMER PROFILING
    # ========================================
    - tab_id: consumer_profiling
      title: "Consumer Profiling"
      subtitle: "Demographics, location patterns & customer segmentation"

      charts:
        # KPI Row
        - key: kpi_total_customers
          title: "Total Customers"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: transaction_count
            y_axis_format: ",.0f"

        - key: kpi_avg_age
          title: "Average Age"
          type: "big_number_total"
          dataset_id: bi_customer_segments
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "32.5"
            y_axis_format: ",.1f"

        - key: kpi_gender_split
          title: "Gender Split (M/F)"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "CONCAT(ROUND(COUNT(CASE WHEN gender='male' THEN 1 END)::FLOAT / COUNT(*) * 100), '/', ROUND(COUNT(CASE WHEN gender='female' THEN 1 END)::FLOAT / COUNT(*) * 100))"

        - key: kpi_urban_pct
          title: "Urban Customers"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: urban_customers
            y_axis_format: ".1%"

        # Gender distribution
        - key: chart_gender_dist
          title: "Gender Distribution"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metric: transaction_count
            groupby: [gender]
            donut: true
            show_labels: true

        # Age distribution
        - key: chart_age_dist
          title: "Age Distribution"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metrics: [transaction_count]
            groupby: [age_bracket]
            y_axis_format: ",.0f"

        # Economic class distribution
        - key: chart_economic_class
          title: "Economic Class Distribution"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 4
          height: 2
          params:
            metrics: [transaction_count]
            groupby: [economic_class]
            y_axis_format: ",.0f"

        # Urban vs Rural
        - key: chart_urban_rural
          title: "Urban vs Rural Split"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metric: transaction_count
            groupby: [store_category]
            donut: true
            show_labels: true

        # Spend by segment
        - key: chart_spend_by_segment
          title: "Average Spend by Income Segment"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [avg_transaction_value]
            groupby: [income_segment]
            y_axis_format: "₱,.2f"

    # ========================================
    # TAB 5: COMPETITIVE ANALYSIS
    # ========================================
    - tab_id: competitive_analysis
      title: "Competitive Analysis"
      subtitle: "Brand-to-brand comparison across categories, geolocation & time periods"

      charts:
        # KPI Row
        - key: kpi_market_position
          title: "Market Position"
          type: "big_number_total"
          dataset_id: bi_competitive_analysis
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "'#2'"

        - key: kpi_market_share
          title: "Market Share"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: tbwa_market_share
            y_axis_format: ".1%"

        - key: kpi_competitive_index
          title: "Competitive Index"
          type: "big_number_total"
          dataset_id: bi_competitive_analysis
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "8.7"

        - key: kpi_store_visit_share
          title: "Store Visit Share"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "35"
            y_axis_format: ".0%"

        # Market share comparison
        - key: chart_market_share
          title: "Brand Market Share Comparison"
          type: "echarts_timeseries_bar"
          dataset_id: bi_competitive_analysis
          width: 12
          height: 3
          params:
            metrics: [total_revenue]
            groupby: [brand_name]
            orientation: horizontal
            row_limit: 10
            order_desc: true
            y_axis_format: "₱,.0f"
            color_scheme: supersetColors

        # TBWA performance by category
        - key: chart_tbwa_by_category
          title: "TBWA Performance by Category"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [tbwa_market_share]
            groupby: [product_category]
            y_axis_format: ".1%"

        # Brand recall rates
        - key: chart_brand_recall
          title: "Brand Recall Rate by Brand"
          type: "echarts_timeseries_bar"
          dataset_id: bi_competitive_analysis
          width: 6
          height: 2
          params:
            metrics:
              - name: brand_recall_pct
                label: "Brand Recall %"
            groupby: [brand_name]
            row_limit: 10
            y_axis_format: ".1%"

    # ========================================
    # TAB 6: GEOGRAPHICAL INTELLIGENCE
    # ========================================
    - tab_id: geographical_intelligence
      title: "Geographical Intelligence"
      subtitle: "Location-based insights, regional performance & market penetration analysis"

      charts:
        # KPI Row
        - key: kpi_top_region
          title: "Top Region"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "'Metro Manila'"

        - key: kpi_regions_covered
          title: "Regional Coverage"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric:
              expressionType: SQL
              sqlExpression: "COUNT(DISTINCT region)"
            y_axis_format: ",.0f"
            subheader: "Regions"

        - key: kpi_total_stores
          title: "Total Stores"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: unique_stores
            y_axis_format: ",.0f"

        - key: kpi_total_market_revenue
          title: "Total Revenue"
          type: "big_number_total"
          dataset_id: bi_fact_transactions
          width: 3
          height: 1
          params:
            metric: total_revenue
            y_axis_format: "₱,.0f"

        # Revenue by region
        - key: chart_revenue_by_region
          title: "Revenue by Region"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 3
          params:
            metrics: [total_revenue]
            groupby: [region]
            orientation: horizontal
            order_desc: true
            y_axis_format: "₱,.0f"

        # Stores by region
        - key: chart_stores_by_region
          title: "Store Count by Region"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 3
          params:
            metrics: [unique_stores]
            groupby: [region]
            orientation: horizontal
            order_desc: true
            y_axis_format: ",.0f"

        # Performance by store type
        - key: chart_by_store_type
          title: "Revenue by Store Type"
          type: "pie"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metric: total_revenue
            groupby: [store_type]
            donut: true
            show_labels: true
            number_format: "₱,.0f"

        # Avg transaction by region
        - key: chart_avg_txn_by_region
          title: "Avg Transaction Value by Region"
          type: "echarts_timeseries_bar"
          dataset_id: bi_fact_transactions
          width: 6
          height: 2
          params:
            metrics: [avg_transaction_value]
            groupby: [region]
            orientation: horizontal
            y_axis_format: "₱,.2f"

        # Store performance table
        - key: table_store_performance
          title: "Store Performance Details"
          type: "table"
          dataset_id: bi_store_performance
          width: 12
          height: 3
          params:
            all_columns:
              - store_id
              - region
              - city
              - store_type
              - transaction_count
              - total_revenue
              - avg_transaction_value
              - avg_handshake_score
              - tbwa_revenue_share
            order_by:
              - column: total_revenue
                order: desc
            page_length: 15
            include_search: true
```

---

## SECTION: IMPLEMENTATION_NOTES

### Step 1: Create Database Tables

The Scout Dashboard requires the following source table:

```sql
CREATE TABLE scout_transactions (
    id VARCHAR(20) PRIMARY KEY,
    store_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    time_of_day VARCHAR(20) NOT NULL CHECK (time_of_day IN ('morning', 'afternoon', 'evening', 'night')),
    location JSONB NOT NULL,
    product_category VARCHAR(100) NOT NULL,
    brand_name VARCHAR(200) NOT NULL,
    sku VARCHAR(300) NOT NULL,
    units_per_transaction INTEGER NOT NULL CHECK (units_per_transaction > 0),
    peso_value NUMERIC(10,2) NOT NULL CHECK (peso_value >= 0),
    basket_size INTEGER NOT NULL CHECK (basket_size > 0),
    combo_basket JSONB NOT NULL DEFAULT '[]',
    request_mode VARCHAR(20) NOT NULL CHECK (request_mode IN ('verbal', 'pointing', 'indirect')),
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('branded', 'unbranded', 'point', 'indirect')),
    suggestion_accepted BOOLEAN NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female', 'unknown')),
    age_bracket VARCHAR(10) NOT NULL CHECK (age_bracket IN ('18-24', '25-34', '35-44', '45-54', '55+', 'unknown')),
    customer_type VARCHAR(20) NOT NULL CHECK (customer_type IN ('regular', 'occasional', 'new', 'unknown')),
    economic_class VARCHAR(10) NOT NULL CHECK (economic_class IN ('A', 'B', 'C', 'D', 'E', 'unknown')),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds >= 0),
    handshake_score NUMERIC(3,2) NOT NULL CHECK (handshake_score >= 0 AND handshake_score <= 1),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('cash', 'gcash', 'maya', 'credit', 'other')),
    store_type VARCHAR(20) NOT NULL CHECK (store_type IN ('urban_high', 'urban_medium', 'residential', 'rural', 'transport', 'other')),
    campaign_influenced BOOLEAN NOT NULL,
    is_tbwa_client BOOLEAN NOT NULL,
    substitution_event JSONB NOT NULL DEFAULT '{"occurred": false, "from": null, "reason": null}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_scout_txn_timestamp ON scout_transactions(timestamp);
CREATE INDEX idx_scout_txn_store ON scout_transactions(store_id);
CREATE INDEX idx_scout_txn_brand ON scout_transactions(brand_name);
CREATE INDEX idx_scout_txn_category ON scout_transactions(product_category);
CREATE INDEX idx_scout_txn_region ON scout_transactions((location->>'region'));
CREATE INDEX idx_scout_txn_tbwa ON scout_transactions(is_tbwa_client);
```

### Step 2: Deploy Gold Views

Execute the SQL views from SCOUT_SQL_VIEWS section in order:

```bash
psql "$EXAMPLES_DB_URI" -f sql/scout_views/V002__create_scout_retail_views.sql
```

### Step 3: Register Datasets in Superset

1. Navigate to **Data > Datasets > + Dataset**
2. For each view in SUPERSET_DATASETS:
   - Select database
   - Select schema: `public`
   - Select table/view
   - Configure metrics and columns per specification

### Step 4: Build Dashboard

1. Create new dashboard: **Scout - Retail Intelligence Dashboard**
2. Create tabs matching the 6 sections
3. Add native filters as specified
4. Build each chart per SCOUT_DASHBOARD_SPEC
5. Arrange layout matching the original Scout Dashboard design

### Dashboard Summary

| Tab | KPIs | Charts |
|-----|------|--------|
| Transaction Trends | Daily Volume, Revenue, Basket Size, Duration | Volume Trends, By Time of Day, By Day |
| Product Mix & SKU | Total SKUs, Active SKUs, Brands, Categories | Category Distribution, Top Brands, Substitutions |
| Consumer Behavior | Conversion, Suggestion Accept, Loyalty, Discovery | Request Methods, Payment Methods, By Segment |
| Consumer Profiling | Customers, Avg Age, Gender Split, Urban % | Demographics, Economic Class, Urban/Rural |
| Competitive Analysis | Market Position, Share, Index, Visit Share | Market Share Comparison, TBWA by Category |
| Geographical Intelligence | Top Region, Coverage, Stores, Revenue | Revenue by Region, Store Performance Table |

---

**End of Scout Dashboard Specification v2.0**
