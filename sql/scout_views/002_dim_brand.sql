-- dim_brand: Brand dimension for Scout Dashboard
-- Source: brands table joined with clients
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_brand CASCADE;

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
