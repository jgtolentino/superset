-- ============================================================================
-- Master Script - Run All SQL Files in Order
-- ============================================================================
--
-- This script creates all example datasets for Superset dashboards.
-- Execute this in your Supabase SQL Editor or via psql.
--
-- Usage:
--   1. Supabase SQL Editor: Copy/paste each file's contents in order
--   2. psql: psql -h <host> -U postgres -d postgres -f run_all.sql
--
-- Order of execution:
--   1. 001_create_schema.sql  - Create examples schema
--   2. 002_messaging_tables.sql - Users, channels, messages, threads
--   3. 003_analytics_tables.sql - Sales, video games, surveys
--   4. 004_geographic_tables.sql - Flights, births, COVID, geography
--   5. 005_views.sql - Virtual datasets (views)
--   6. 006_sample_data.sql - Sample data for all tables
-- ============================================================================

\echo '=== Creating Examples Schema ==='
\i 001_create_schema.sql

\echo '=== Creating Messaging Tables ==='
\i 002_messaging_tables.sql

\echo '=== Creating Analytics Tables ==='
\i 003_analytics_tables.sql

\echo '=== Creating Geographic Tables ==='
\i 004_geographic_tables.sql

\echo '=== Creating Views ==='
\i 005_views.sql

\echo '=== Loading Sample Data ==='
\i 006_sample_data.sql

\echo '=== All datasets created successfully! ==='
