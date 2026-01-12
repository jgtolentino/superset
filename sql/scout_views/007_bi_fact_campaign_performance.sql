-- bi_fact_campaign_performance: Core performance fact for Scout Dashboard
-- Combines campaign performance with spend data and all dimension attributes
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.bi_fact_campaign_performance CASCADE;

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
