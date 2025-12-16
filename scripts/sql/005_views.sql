-- ============================================================================
-- Virtual Datasets (Views)
-- Views: users_channels, messages_channels, new_members_daily,
--        members_channels_2, hierarchical_dataset
-- ============================================================================

SET search_path TO examples, public;

-- ----------------------------------------------------------------------------
-- users_channels view (join users with their channel memberships)
-- This corresponds to "users_channels-uzooNNtSRO" virtual dataset
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS examples.v_users_channels CASCADE;
CREATE OR REPLACE VIEW examples.v_users_channels AS
SELECT
    u.id AS user_id,
    u.username,
    u.full_name,
    u.email,
    u.status AS user_status,
    c.id AS channel_id,
    c.name AS channel_name,
    c.channel_type,
    cm.role AS member_role,
    cm.joined_at,
    cm.last_read_at,
    cm.notifications_enabled
FROM examples.users u
JOIN examples.channel_members cm ON u.id = cm.user_id
JOIN examples.channels c ON cm.channel_id = c.id;

-- ----------------------------------------------------------------------------
-- messages_channels view (messages with channel info)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS examples.v_messages_channels CASCADE;
CREATE OR REPLACE VIEW examples.v_messages_channels AS
SELECT
    m.id AS message_id,
    m.content,
    m.message_type,
    m.created_at AS message_time,
    m.is_edited,
    m.reaction_count,
    c.id AS channel_id,
    c.name AS channel_name,
    c.channel_type,
    u.id AS user_id,
    u.username AS author,
    u.full_name AS author_name,
    t.id AS thread_id,
    t.title AS thread_title
FROM examples.messages m
JOIN examples.channels c ON m.channel_id = c.id
LEFT JOIN examples.users u ON m.user_id = u.id
LEFT JOIN examples.threads t ON m.thread_id = t.id;

-- ----------------------------------------------------------------------------
-- new_members_daily view (daily new member signups)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS examples.v_new_members_daily CASCADE;
CREATE OR REPLACE VIEW examples.v_new_members_daily AS
SELECT
    DATE(cm.joined_at) AS signup_date,
    COUNT(*) AS new_members,
    COUNT(DISTINCT cm.channel_id) AS channels_joined,
    COUNT(DISTINCT cm.user_id) AS unique_users
FROM examples.channel_members cm
GROUP BY DATE(cm.joined_at)
ORDER BY signup_date DESC;

-- ----------------------------------------------------------------------------
-- members_channels_2 view (enhanced member-channel analytics)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS examples.v_members_channels_2 CASCADE;
CREATE OR REPLACE VIEW examples.v_members_channels_2 AS
SELECT
    c.id AS channel_id,
    c.name AS channel_name,
    c.channel_type,
    c.created_at AS channel_created,
    COUNT(DISTINCT cm.user_id) AS total_members,
    COUNT(DISTINCT CASE WHEN cm.role = 'admin' THEN cm.user_id END) AS admin_count,
    COUNT(DISTINCT CASE WHEN cm.role = 'owner' THEN cm.user_id END) AS owner_count,
    MIN(cm.joined_at) AS first_member_joined,
    MAX(cm.joined_at) AS last_member_joined,
    AVG(EXTRACT(EPOCH FROM (NOW() - cm.joined_at)) / 86400)::INTEGER AS avg_member_tenure_days
FROM examples.channels c
LEFT JOIN examples.channel_members cm ON c.id = cm.channel_id
GROUP BY c.id, c.name, c.channel_type, c.created_at;

-- ----------------------------------------------------------------------------
-- hierarchical_dataset view (for treemap/hierarchy visualizations)
-- This goes in the public schema as per the original dataset
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS public.hierarchical_dataset CASCADE;
CREATE OR REPLACE VIEW public.hierarchical_dataset AS
SELECT
    region AS level_1,
    country_name AS level_2,
    income_group AS level_3,
    SUM(population) AS total_population,
    AVG(life_expectancy) AS avg_life_expectancy,
    AVG(gdp_per_capita) AS avg_gdp_per_capita,
    COUNT(DISTINCT country_code) AS country_count
FROM examples.wb_health_population
WHERE year = (SELECT MAX(year) FROM examples.wb_health_population)
GROUP BY region, country_name, income_group;

-- Grant access to views
GRANT SELECT ON examples.v_users_channels TO anon, authenticated, service_role;
GRANT SELECT ON examples.v_messages_channels TO anon, authenticated, service_role;
GRANT SELECT ON examples.v_new_members_daily TO anon, authenticated, service_role;
GRANT SELECT ON examples.v_members_channels_2 TO anon, authenticated, service_role;
GRANT SELECT ON public.hierarchical_dataset TO anon, authenticated, service_role;
