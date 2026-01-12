-- V001__create_scout_dashboard_views.sql
-- Scout Dashboard Gold Views for Apache Superset
--
-- Description: Creates all dimension and fact views required for the
--              Scout Agency Performance Overview dashboard.
--
-- Dependencies: Requires existing source tables from TBWA Agency Databank:
--   - clients, brands, campaigns, channels, markets, date_dim
--   - campaign_performance, media_spend
--
-- Usage: Execute against the databank database (PostgreSQL)
--   psql "$EXAMPLES_DB_URI" -f V001__create_scout_dashboard_views.sql
--
-- Version: 1.0
-- Generated: 2026-01-12

BEGIN;

-- ============================================
-- DROP EXISTING VIEWS (for idempotency)
-- ============================================
DROP VIEW IF EXISTS public.bi_campaign_summary CASCADE;
DROP VIEW IF EXISTS public.bi_fact_campaign_performance CASCADE;
DROP VIEW IF EXISTS public.dim_time CASCADE;
DROP VIEW IF EXISTS public.dim_market CASCADE;
DROP VIEW IF EXISTS public.dim_channel CASCADE;
DROP VIEW IF EXISTS public.dim_campaign CASCADE;
DROP VIEW IF EXISTS public.dim_brand CASCADE;
DROP VIEW IF EXISTS public.dim_client CASCADE;

-- ============================================
-- DIMENSION VIEWS
-- ============================================

-- 1. dim_client: Client dimension
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

-- 2. dim_brand: Brand dimension with client denormalization
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

-- 3. dim_campaign: Campaign dimension with brand and client denormalization
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

-- 4. dim_channel: Media channel dimension
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

-- 5. dim_market: Geographic market dimension
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

-- 6. dim_time: Time/date dimension
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

-- ============================================
-- FACT VIEWS
-- ============================================

-- 7. bi_fact_campaign_performance: Core performance fact
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

-- 8. bi_campaign_summary: Campaign-level aggregated summary
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

-- ============================================
-- PERMISSIONS (if superset_readonly role exists)
-- ============================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'superset_readonly') THEN
        GRANT SELECT ON public.dim_client TO superset_readonly;
        GRANT SELECT ON public.dim_brand TO superset_readonly;
        GRANT SELECT ON public.dim_campaign TO superset_readonly;
        GRANT SELECT ON public.dim_channel TO superset_readonly;
        GRANT SELECT ON public.dim_market TO superset_readonly;
        GRANT SELECT ON public.dim_time TO superset_readonly;
        GRANT SELECT ON public.bi_fact_campaign_performance TO superset_readonly;
        GRANT SELECT ON public.bi_campaign_summary TO superset_readonly;
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
        'dim_client', 'dim_brand', 'dim_campaign', 'dim_channel',
        'dim_market', 'dim_time', 'bi_fact_campaign_performance', 'bi_campaign_summary'
    );

    IF view_count = 8 THEN
        RAISE NOTICE 'SUCCESS: All 8 Scout Dashboard views created successfully';
    ELSE
        RAISE EXCEPTION 'ERROR: Expected 8 views, found %', view_count;
    END IF;
END $$;

COMMIT;
