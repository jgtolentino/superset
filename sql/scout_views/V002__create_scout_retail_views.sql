-- V002__create_scout_retail_views.sql
-- Scout Retail Intelligence Views for Apache Superset
--
-- Description: Creates all analytics views for the Scout Dashboard
--              powered by TBWA\SMP Suqi Analytics retail intelligence platform.
--
-- Source: scout_transactions table (mirrors Odoo ipai.scout_transaction model)
--
-- Dependencies:
--   - scout_transactions table with 26-field schema per Data Dictionary
--
-- Usage:
--   psql "$EXAMPLES_DB_URI" -f V002__create_scout_retail_views.sql
--
-- Version: 2.0
-- Generated: 2026-01-12
-- Platform: TBWA\SMP Suqi Analytics - Retail Intelligence

BEGIN;

-- ============================================
-- DROP EXISTING VIEWS (for idempotency)
-- ============================================
DROP VIEW IF EXISTS public.bi_competitive_analysis CASCADE;
DROP VIEW IF EXISTS public.bi_store_performance CASCADE;
DROP VIEW IF EXISTS public.bi_customer_segments CASCADE;
DROP VIEW IF EXISTS public.bi_product_performance CASCADE;
DROP VIEW IF EXISTS public.bi_transaction_summary_daily CASCADE;
DROP VIEW IF EXISTS public.bi_fact_transactions CASCADE;
DROP VIEW IF EXISTS public.dim_geography CASCADE;
DROP VIEW IF EXISTS public.dim_time CASCADE;
DROP VIEW IF EXISTS public.dim_product CASCADE;
DROP VIEW IF EXISTS public.dim_store CASCADE;

-- ============================================
-- DIMENSION VIEWS
-- ============================================

-- 1. dim_store: Store dimension derived from transaction locations
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
    END AS store_category,
    CASE store_type
        WHEN 'urban_high' THEN 1
        WHEN 'urban_medium' THEN 2
        WHEN 'residential' THEN 3
        WHEN 'rural' THEN 4
        WHEN 'transport' THEN 5
        ELSE 6
    END AS store_type_order
FROM scout_transactions
WHERE store_id IS NOT NULL;

COMMENT ON VIEW public.dim_store IS 'Store dimension for Scout Dashboard - derived from transaction locations';

-- 2. dim_product: Product/SKU dimension
CREATE OR REPLACE VIEW public.dim_product AS
SELECT DISTINCT
    sku,
    brand_name,
    product_category,
    is_tbwa_client,
    CASE
        WHEN is_tbwa_client = TRUE THEN 'TBWA Client'
        ELSE 'Competitor'
    END AS brand_type,
    CASE product_category
        WHEN 'Beverages' THEN 1
        WHEN 'Snacks' THEN 2
        WHEN 'Tobacco' THEN 3
        WHEN 'Personal Care' THEN 4
        WHEN 'Household' THEN 5
        ELSE 99
    END AS category_order
FROM scout_transactions
WHERE sku IS NOT NULL;

COMMENT ON VIEW public.dim_product IS 'Product/SKU dimension for Scout Dashboard';

-- 3. dim_time: Time dimension from transaction timestamps
CREATE OR REPLACE VIEW public.dim_time AS
SELECT DISTINCT
    DATE(timestamp) AS date_key,
    EXTRACT(YEAR FROM timestamp)::INTEGER AS year,
    EXTRACT(QUARTER FROM timestamp)::INTEGER AS quarter,
    EXTRACT(MONTH FROM timestamp)::INTEGER AS month,
    TRIM(TO_CHAR(timestamp, 'Month')) AS month_name,
    EXTRACT(WEEK FROM timestamp)::INTEGER AS week,
    EXTRACT(DOW FROM timestamp)::INTEGER AS day_of_week,
    TRIM(TO_CHAR(timestamp, 'Day')) AS day_name,
    CASE WHEN EXTRACT(DOW FROM timestamp) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    TO_CHAR(timestamp, 'YYYY') || '-Q' || EXTRACT(QUARTER FROM timestamp)::TEXT AS year_quarter,
    TO_CHAR(timestamp, 'YYYY-MM') AS year_month
FROM scout_transactions
WHERE timestamp IS NOT NULL;

COMMENT ON VIEW public.dim_time IS 'Time dimension for Scout Dashboard - calendar attributes';

-- 4. dim_geography: Philippine geographic hierarchy
CREATE OR REPLACE VIEW public.dim_geography AS
SELECT DISTINCT
    COALESCE(location->>'region', 'Unknown') AS region,
    COALESCE(location->>'province', 'Unknown') AS province,
    COALESCE(location->>'city', 'Unknown') AS city,
    COALESCE(location->>'barangay', 'Unknown') AS barangay,
    COALESCE(location->>'region', 'Unknown') || ' > ' ||
    COALESCE(location->>'province', '') || ' > ' ||
    COALESCE(location->>'city', '') AS geo_hierarchy,
    CASE COALESCE(location->>'region', 'Unknown')
        WHEN 'NCR' THEN 1
        WHEN 'Metro Manila' THEN 1
        WHEN 'CALABARZON' THEN 2
        WHEN 'Central Luzon' THEN 3
        WHEN 'Central Visayas' THEN 4
        WHEN 'Western Visayas' THEN 5
        WHEN 'Davao Region' THEN 6
        ELSE 99
    END AS region_order
FROM scout_transactions
WHERE location IS NOT NULL;

COMMENT ON VIEW public.dim_geography IS 'Philippine geographic hierarchy dimension for Scout Dashboard';

-- ============================================
-- MAIN FACT VIEW
-- ============================================

-- 5. bi_fact_transactions: Core retail transaction fact
CREATE OR REPLACE VIEW public.bi_fact_transactions AS
SELECT
    -- Transaction identifiers
    t.id AS transaction_id,
    t.store_id,
    t.timestamp,
    DATE(t.timestamp) AS transaction_date,
    t.time_of_day,

    -- Time dimensions (denormalized)
    EXTRACT(YEAR FROM t.timestamp)::INTEGER AS year,
    EXTRACT(QUARTER FROM t.timestamp)::INTEGER AS quarter,
    EXTRACT(MONTH FROM t.timestamp)::INTEGER AS month,
    TRIM(TO_CHAR(t.timestamp, 'Month')) AS month_name,
    EXTRACT(WEEK FROM t.timestamp)::INTEGER AS week,
    EXTRACT(DOW FROM t.timestamp)::INTEGER AS day_of_week,
    TRIM(TO_CHAR(t.timestamp, 'Day')) AS day_name,
    CASE WHEN EXTRACT(DOW FROM t.timestamp) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    EXTRACT(HOUR FROM t.timestamp)::INTEGER AS hour_of_day,

    -- Location dimensions (denormalized from JSON)
    COALESCE(t.location->>'region', 'Unknown') AS region,
    COALESCE(t.location->>'province', 'Unknown') AS province,
    COALESCE(t.location->>'city', 'Unknown') AS city,
    COALESCE(t.location->>'barangay', 'Unknown') AS barangay,

    -- Store dimensions
    t.store_type,
    t.economic_class,
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
    CASE t.economic_class
        WHEN 'A' THEN 'High'
        WHEN 'B' THEN 'High'
        WHEN 'C' THEN 'Middle'
        WHEN 'D' THEN 'Low'
        WHEN 'E' THEN 'Low'
        ELSE 'Unknown'
    END AS income_segment,

    -- Behavior dimensions
    t.request_mode,
    t.request_type,
    t.suggestion_accepted,
    t.payment_method,
    t.campaign_influenced,

    -- Substitution event (parsed from JSON)
    COALESCE((t.substitution_event->>'occurred')::BOOLEAN, FALSE) AS substitution_occurred,
    t.substitution_event->>'from' AS substitution_from,
    t.substitution_event->>'reason' AS substitution_reason,

    -- Core metrics
    COALESCE(t.units_per_transaction, 0) AS units_per_transaction,
    COALESCE(t.peso_value, 0) AS peso_value,
    COALESCE(t.basket_size, 1) AS basket_size,
    COALESCE(t.duration_seconds, 0) AS duration_seconds,
    COALESCE(t.handshake_score, 0) AS handshake_score,

    -- Derived flags
    CASE WHEN t.basket_size >= 3 THEN TRUE ELSE FALSE END AS is_multi_item_basket,
    CASE WHEN t.customer_type = 'regular' THEN TRUE ELSE FALSE END AS is_repeat_customer,
    CASE WHEN t.payment_method IN ('gcash', 'maya') THEN TRUE ELSE FALSE END AS is_digital_payment,

    -- Combo basket (array length if available)
    COALESCE(jsonb_array_length(t.combo_basket), 0) AS combo_items_count

FROM scout_transactions t;

COMMENT ON VIEW public.bi_fact_transactions IS 'Main fact view for Scout Dashboard - retail transactions with all dimensions denormalized';

-- ============================================
-- AGGREGATED SUMMARY VIEWS
-- ============================================

-- 6. bi_transaction_summary_daily: Daily aggregated summary
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
    COUNT(DISTINCT sku) AS active_skus,
    COUNT(DISTINCT brand_name) AS active_brands,

    -- Revenue metrics
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY peso_value) AS median_transaction_value,

    -- Basket metrics
    SUM(units_per_transaction) AS total_units,
    AVG(basket_size) AS avg_basket_size,
    SUM(CASE WHEN basket_size >= 3 THEN 1 ELSE 0 END) AS multi_item_baskets,

    -- Duration metrics
    AVG(duration_seconds) AS avg_duration,
    AVG(handshake_score) AS avg_handshake_score,

    -- Customer demographics
    COUNT(CASE WHEN gender = 'male' THEN 1 END) AS male_customers,
    COUNT(CASE WHEN gender = 'female' THEN 1 END) AS female_customers,
    COUNT(CASE WHEN customer_type = 'regular' THEN 1 END) AS repeat_customers,
    COUNT(CASE WHEN customer_type = 'new' THEN 1 END) AS new_customers,

    -- Behavior metrics
    SUM(CASE WHEN suggestion_accepted THEN 1 ELSE 0 END) AS suggestions_accepted,
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END) AS branded_requests,
    SUM(CASE WHEN campaign_influenced THEN 1 ELSE 0 END) AS campaign_influenced_count,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN THEN 1 ELSE 0 END) AS substitution_count,

    -- Payment methods
    SUM(CASE WHEN payment_method = 'cash' THEN 1 ELSE 0 END) AS cash_payments,
    SUM(CASE WHEN payment_method IN ('gcash', 'maya') THEN 1 ELSE 0 END) AS digital_payments,

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

-- 7. bi_product_performance: Product/SKU performance
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
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN store_id || gender || age_bracket END) AS repeat_buyers,

    -- Behavior metrics
    AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100 AS suggestion_acceptance_rate,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND substitution_event->>'from' = brand_name THEN 1 ELSE 0 END) AS substituted_away,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND brand_name != COALESCE(substitution_event->>'from', '') THEN 1 ELSE 0 END) AS substituted_to,

    -- Request patterns
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS branded_request_pct,

    -- Time range
    MIN(timestamp) AS first_sale,
    MAX(timestamp) AS last_sale

FROM scout_transactions
GROUP BY brand_name, product_category, sku, is_tbwa_client;

COMMENT ON VIEW public.bi_product_performance IS 'Product/SKU performance metrics for Scout Dashboard';

-- 8. bi_customer_segments: Customer segment analysis
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
    SUM(CASE WHEN request_mode = 'verbal' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS verbal_request_pct,
    SUM(CASE WHEN request_mode = 'pointing' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS pointing_request_pct,
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS branded_request_pct,

    -- Payment
    SUM(CASE WHEN payment_method = 'cash' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS cash_payment_pct,
    SUM(CASE WHEN payment_method IN ('gcash', 'maya') THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS digital_payment_pct,

    -- Category preferences
    MODE() WITHIN GROUP (ORDER BY product_category) AS top_category

FROM scout_transactions
GROUP BY gender, age_bracket, economic_class, customer_type;

COMMENT ON VIEW public.bi_customer_segments IS 'Customer segment analysis for Scout Dashboard';

-- 9. bi_store_performance: Store-level performance
CREATE OR REPLACE VIEW public.bi_store_performance AS
SELECT
    store_id,
    store_type,
    economic_class,
    COALESCE(location->>'region', 'Unknown') AS region,
    COALESCE(location->>'province', 'Unknown') AS province,
    COALESCE(location->>'city', 'Unknown') AS city,
    COALESCE(location->>'barangay', 'Unknown') AS barangay,
    CASE store_type
        WHEN 'urban_high' THEN 'Urban'
        WHEN 'urban_medium' THEN 'Urban'
        WHEN 'residential' THEN 'Suburban'
        WHEN 'rural' THEN 'Rural'
        WHEN 'transport' THEN 'Transit'
        ELSE 'Other'
    END AS store_category,

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
    COUNT(DISTINCT CASE WHEN customer_type = 'regular' THEN gender || age_bracket END) AS repeat_customer_segments,
    AVG(CASE WHEN customer_type = 'regular' THEN 1.0 ELSE 0.0 END) * 100 AS repeat_customer_pct,

    -- Performance
    AVG(handshake_score) AS avg_handshake_score,
    AVG(CASE WHEN suggestion_accepted THEN 1.0 ELSE 0.0 END) * 100 AS suggestion_acceptance_rate,
    AVG(duration_seconds) AS avg_duration,

    -- TBWA share
    SUM(CASE WHEN is_tbwa_client THEN peso_value ELSE 0 END)::FLOAT /
        NULLIF(SUM(peso_value), 0) * 100 AS tbwa_revenue_share,

    -- Digital payment adoption
    SUM(CASE WHEN payment_method IN ('gcash', 'maya') THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS digital_payment_rate,

    -- Time range
    MIN(timestamp) AS first_transaction,
    MAX(timestamp) AS last_transaction

FROM scout_transactions
GROUP BY
    store_id,
    store_type,
    economic_class,
    COALESCE(location->>'region', 'Unknown'),
    COALESCE(location->>'province', 'Unknown'),
    COALESCE(location->>'city', 'Unknown'),
    COALESCE(location->>'barangay', 'Unknown');

COMMENT ON VIEW public.bi_store_performance IS 'Store-level performance metrics for Scout Dashboard';

-- 10. bi_competitive_analysis: Brand competitive analysis
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
    COUNT(DISTINCT COALESCE(location->>'region', 'Unknown')) AS region_count,

    -- Customer metrics
    COUNT(DISTINCT CASE WHEN customer_type = 'regular'
                        THEN gender || age_bracket END) AS loyal_customer_segments,

    -- Substitution dynamics
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND substitution_event->>'from' = brand_name THEN 1 ELSE 0 END) AS lost_to_substitution,
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND brand_name != COALESCE(substitution_event->>'from', '') THEN 1 ELSE 0 END) AS gained_from_substitution,

    -- Net substitution flow
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND brand_name != COALESCE(substitution_event->>'from', '') THEN 1 ELSE 0 END) -
    SUM(CASE WHEN (substitution_event->>'occurred')::BOOLEAN
             AND substitution_event->>'from' = brand_name THEN 1 ELSE 0 END) AS net_substitution_flow,

    -- Request type (brand strength indicator)
    SUM(CASE WHEN request_type = 'branded' THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(COUNT(*), 0) * 100 AS brand_recall_pct,

    -- Campaign effectiveness
    SUM(CASE WHEN campaign_influenced THEN peso_value ELSE 0 END) AS campaign_influenced_revenue,
    AVG(CASE WHEN campaign_influenced THEN 1.0 ELSE 0.0 END) * 100 AS campaign_attribution_rate

FROM scout_transactions
GROUP BY product_category, brand_name, is_tbwa_client;

COMMENT ON VIEW public.bi_competitive_analysis IS 'Brand competitive analysis for Scout Dashboard';

-- ============================================
-- ADDITIONAL ANALYTICS VIEWS
-- ============================================

-- 11. bi_hourly_patterns: Time-of-day analysis
CREATE OR REPLACE VIEW public.bi_hourly_patterns AS
SELECT
    time_of_day,
    EXTRACT(HOUR FROM timestamp)::INTEGER AS hour_of_day,
    CASE EXTRACT(DOW FROM timestamp)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    CASE WHEN EXTRACT(DOW FROM timestamp) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,

    COUNT(*) AS transaction_count,
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,
    AVG(basket_size) AS avg_basket_size,
    AVG(duration_seconds) AS avg_duration

FROM scout_transactions
GROUP BY
    time_of_day,
    EXTRACT(HOUR FROM timestamp),
    EXTRACT(DOW FROM timestamp);

COMMENT ON VIEW public.bi_hourly_patterns IS 'Hourly transaction patterns for Scout Dashboard';

-- 12. bi_basket_analysis: Multi-item basket analysis
CREATE OR REPLACE VIEW public.bi_basket_analysis AS
SELECT
    basket_size,
    CASE
        WHEN basket_size = 1 THEN 'Single Item'
        WHEN basket_size = 2 THEN 'Dual Item'
        WHEN basket_size BETWEEN 3 AND 5 THEN '3-5 Items'
        ELSE '6+ Items'
    END AS basket_category,

    COUNT(*) AS transaction_count,
    SUM(peso_value) AS total_revenue,
    AVG(peso_value) AS avg_transaction_value,
    AVG(units_per_transaction) AS avg_units,
    AVG(duration_seconds) AS avg_duration,

    -- Customer profile
    MODE() WITHIN GROUP (ORDER BY age_bracket) AS dominant_age_bracket,
    MODE() WITHIN GROUP (ORDER BY economic_class) AS dominant_economic_class,

    -- TBWA presence
    AVG(CASE WHEN is_tbwa_client THEN 1.0 ELSE 0.0 END) * 100 AS tbwa_presence_pct

FROM scout_transactions
GROUP BY basket_size;

COMMENT ON VIEW public.bi_basket_analysis IS 'Basket size analysis for Scout Dashboard';

-- ============================================
-- PERMISSIONS
-- ============================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'superset_readonly') THEN
        GRANT SELECT ON public.dim_store TO superset_readonly;
        GRANT SELECT ON public.dim_product TO superset_readonly;
        GRANT SELECT ON public.dim_time TO superset_readonly;
        GRANT SELECT ON public.dim_geography TO superset_readonly;
        GRANT SELECT ON public.bi_fact_transactions TO superset_readonly;
        GRANT SELECT ON public.bi_transaction_summary_daily TO superset_readonly;
        GRANT SELECT ON public.bi_product_performance TO superset_readonly;
        GRANT SELECT ON public.bi_customer_segments TO superset_readonly;
        GRANT SELECT ON public.bi_store_performance TO superset_readonly;
        GRANT SELECT ON public.bi_competitive_analysis TO superset_readonly;
        GRANT SELECT ON public.bi_hourly_patterns TO superset_readonly;
        GRANT SELECT ON public.bi_basket_analysis TO superset_readonly;
        RAISE NOTICE 'Granted SELECT permissions to superset_readonly role';
    END IF;
END $$;

-- ============================================
-- VALIDATION
-- ============================================
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public'
    AND table_name IN (
        'dim_store', 'dim_product', 'dim_time', 'dim_geography',
        'bi_fact_transactions', 'bi_transaction_summary_daily',
        'bi_product_performance', 'bi_customer_segments',
        'bi_store_performance', 'bi_competitive_analysis',
        'bi_hourly_patterns', 'bi_basket_analysis'
    );

    IF view_count = 12 THEN
        RAISE NOTICE 'SUCCESS: All 12 Scout Retail Intelligence views created successfully';
    ELSE
        RAISE EXCEPTION 'ERROR: Expected 12 views, found %', view_count;
    END IF;
END $$;

COMMIT;
