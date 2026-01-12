-- dim_campaign: Campaign dimension for Scout Dashboard
-- Source: campaigns table joined with brands and clients
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_campaign CASCADE;

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
