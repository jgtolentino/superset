-- dim_client: Client dimension for Scout Dashboard
-- Source: clients table from TBWA Agency Databank
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_client CASCADE;

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
