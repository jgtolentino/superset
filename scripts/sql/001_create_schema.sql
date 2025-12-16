-- ============================================================================
-- Superset Example Datasets - Schema Setup
-- Target: Supabase PostgreSQL (examples schema)
-- ============================================================================

-- Create the examples schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS examples;

-- Set search path for this session
SET search_path TO examples, public;

-- Grant usage on schema
GRANT USAGE ON SCHEMA examples TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA examples TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA examples GRANT ALL ON TABLES TO anon, authenticated, service_role;
