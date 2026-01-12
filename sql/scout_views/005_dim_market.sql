-- dim_market: Geographic market dimension for Scout Dashboard
-- Source: markets table
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_market CASCADE;

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
