-- dim_channel: Media channel dimension for Scout Dashboard
-- Source: channels table
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_channel CASCADE;

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
