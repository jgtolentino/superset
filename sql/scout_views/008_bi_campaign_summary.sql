-- bi_campaign_summary: Campaign-level aggregated summary for Scout Dashboard
-- Pre-aggregated metrics at campaign level for high-level reporting
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.bi_campaign_summary CASCADE;

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
