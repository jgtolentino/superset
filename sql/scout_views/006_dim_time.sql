-- dim_time: Time/date dimension for Scout Dashboard
-- Source: date_dim table or generated
-- Version: 1.0
-- Generated: 2026-01-12

DROP VIEW IF EXISTS public.dim_time CASCADE;

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
