-- Migration: 003_create_rls_policies.sql
-- Description: Row-Level Security policies for multi-tenant isolation
-- Author: InsightPulse AI
-- Date: 2026-01-13
--
-- This migration creates RLS policies for Supabase/PostgreSQL that enforce:
--   1. Tenant isolation: Users can only see data for their own account
--   2. Provider visibility: Providers can see subscription data for their services
--   3. Cross-tenant relationships via explicit account_links
--
-- Prerequisites:
--   - Migration 002 must be applied first
--   - For Supabase: auth.uid() returns the authenticated user's UUID
--   - For custom JWT: Use current_setting('app.current_user_id') or similar
--
-- Usage:
--   - Set the session variable: SET app.current_account_id = 'uuid-here';
--   - Or use Supabase auth: auth.jwt() -> 'account_id'

BEGIN;

-- Record migration
INSERT INTO public.schema_migrations (version) VALUES ('003_create_rls_policies')
ON CONFLICT (version) DO NOTHING;

----------------------------------------------------------------------------
-- HELPER FUNCTIONS
----------------------------------------------------------------------------

-- Get current account ID from session or JWT
-- This function should be customized based on your auth setup
CREATE OR REPLACE FUNCTION public.get_current_account_id()
RETURNS UUID AS $$
BEGIN
    -- Option 1: From session variable (for direct database connections)
    IF current_setting('app.current_account_id', true) IS NOT NULL
       AND current_setting('app.current_account_id', true) != '' THEN
        RETURN current_setting('app.current_account_id', true)::UUID;
    END IF;

    -- Option 2: From Supabase JWT (uncomment if using Supabase)
    -- RETURN (auth.jwt() ->> 'account_id')::UUID;

    -- Option 3: From auth.users metadata (uncomment if using Supabase)
    -- RETURN (
    --     SELECT (raw_user_meta_data ->> 'account_id')::UUID
    --     FROM auth.users
    --     WHERE id = auth.uid()
    -- );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Get current user ID from session or JWT
CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS UUID AS $$
BEGIN
    -- Option 1: From session variable
    IF current_setting('app.current_user_id', true) IS NOT NULL
       AND current_setting('app.current_user_id', true) != '' THEN
        RETURN current_setting('app.current_user_id', true)::UUID;
    END IF;

    -- Option 2: From Supabase auth (uncomment if using Supabase)
    -- RETURN auth.uid();

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Check if user is admin for their account
CREATE OR REPLACE FUNCTION public.is_current_user_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.users
        WHERE id = public.get_current_user_id()
        AND is_admin = TRUE
        AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Check if account has provider role
CREATE OR REPLACE FUNCTION public.account_is_provider(account_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.account_roles
        WHERE account_id = account_uuid
        AND role = 'PROVIDER'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Check if current account can access another account (via link or self)
CREATE OR REPLACE FUNCTION public.can_access_account(target_account_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_account UUID;
BEGIN
    current_account := public.get_current_account_id();

    -- Can always access own account
    IF current_account = target_account_id THEN
        RETURN TRUE;
    END IF;

    -- Check for provider relationship
    IF EXISTS (
        SELECT 1 FROM public.account_links
        WHERE from_account_id = current_account
        AND to_account_id = target_account_id
        AND link_type = 'PROVIDER_OF'
    ) THEN
        RETURN TRUE;
    END IF;

    -- Check for partner relationship (symmetric)
    IF EXISTS (
        SELECT 1 FROM public.account_links
        WHERE (
            (from_account_id = current_account AND to_account_id = target_account_id)
            OR
            (from_account_id = target_account_id AND to_account_id = current_account)
        )
        AND link_type = 'PARTNER_OF'
    ) THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

----------------------------------------------------------------------------
-- ENABLE RLS ON ALL TABLES
----------------------------------------------------------------------------

ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.services ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.service_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.environments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

----------------------------------------------------------------------------
-- ACCOUNTS POLICIES
----------------------------------------------------------------------------

-- Users can see their own account
DROP POLICY IF EXISTS accounts_own_account ON public.accounts;
CREATE POLICY accounts_own_account ON public.accounts
    FOR SELECT
    USING (id = public.get_current_account_id());

-- Users can see accounts they have a link to (provider, partner, etc.)
DROP POLICY IF EXISTS accounts_linked_accounts ON public.accounts;
CREATE POLICY accounts_linked_accounts ON public.accounts
    FOR SELECT
    USING (public.can_access_account(id));

-- Only account admins can update their own account
DROP POLICY IF EXISTS accounts_admin_update ON public.accounts;
CREATE POLICY accounts_admin_update ON public.accounts
    FOR UPDATE
    USING (id = public.get_current_account_id() AND public.is_current_user_admin())
    WITH CHECK (id = public.get_current_account_id());

----------------------------------------------------------------------------
-- ACCOUNT_ROLES POLICIES
----------------------------------------------------------------------------

-- Users can see roles for their own account
DROP POLICY IF EXISTS account_roles_own_account ON public.account_roles;
CREATE POLICY account_roles_own_account ON public.account_roles
    FOR SELECT
    USING (account_id = public.get_current_account_id());

-- Users can see roles for linked accounts
DROP POLICY IF EXISTS account_roles_linked_accounts ON public.account_roles;
CREATE POLICY account_roles_linked_accounts ON public.account_roles
    FOR SELECT
    USING (public.can_access_account(account_id));

-- Only account admins can modify roles
DROP POLICY IF EXISTS account_roles_admin_all ON public.account_roles;
CREATE POLICY account_roles_admin_all ON public.account_roles
    FOR ALL
    USING (account_id = public.get_current_account_id() AND public.is_current_user_admin())
    WITH CHECK (account_id = public.get_current_account_id());

----------------------------------------------------------------------------
-- USERS POLICIES
----------------------------------------------------------------------------

-- Users can see users in their own account
DROP POLICY IF EXISTS users_own_account ON public.users;
CREATE POLICY users_own_account ON public.users
    FOR SELECT
    USING (account_id = public.get_current_account_id());

-- Users can update their own profile
DROP POLICY IF EXISTS users_own_profile ON public.users;
CREATE POLICY users_own_profile ON public.users
    FOR UPDATE
    USING (id = public.get_current_user_id())
    WITH CHECK (id = public.get_current_user_id() AND account_id = public.get_current_account_id());

-- Account admins can manage all users in their account
DROP POLICY IF EXISTS users_admin_all ON public.users;
CREATE POLICY users_admin_all ON public.users
    FOR ALL
    USING (account_id = public.get_current_account_id() AND public.is_current_user_admin())
    WITH CHECK (account_id = public.get_current_account_id());

----------------------------------------------------------------------------
-- SERVICES POLICIES
----------------------------------------------------------------------------

-- Anyone can see public services
DROP POLICY IF EXISTS services_public ON public.services;
CREATE POLICY services_public ON public.services
    FOR SELECT
    USING (is_public = TRUE);

-- Providers can see their own services
DROP POLICY IF EXISTS services_own_provider ON public.services;
CREATE POLICY services_own_provider ON public.services
    FOR SELECT
    USING (provider_account_id = public.get_current_account_id());

-- Tenants can see services they're subscribed to
DROP POLICY IF EXISTS services_subscribed ON public.services;
CREATE POLICY services_subscribed ON public.services
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.subscriptions
            WHERE service_id = services.id
            AND tenant_account_id = public.get_current_account_id()
            AND status IN ('ACTIVE', 'DRAFT')
        )
    );

-- Providers can manage their own services
DROP POLICY IF EXISTS services_provider_manage ON public.services;
CREATE POLICY services_provider_manage ON public.services
    FOR ALL
    USING (
        provider_account_id = public.get_current_account_id()
        AND public.account_is_provider(public.get_current_account_id())
    )
    WITH CHECK (
        provider_account_id = public.get_current_account_id()
        AND public.account_is_provider(public.get_current_account_id())
    );

----------------------------------------------------------------------------
-- SERVICE_PLANS POLICIES
----------------------------------------------------------------------------

-- Anyone can see plans for public services
DROP POLICY IF EXISTS service_plans_public ON public.service_plans;
CREATE POLICY service_plans_public ON public.service_plans
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.services
            WHERE id = service_plans.service_id
            AND is_public = TRUE
        )
    );

-- Providers can see and manage their own service plans
DROP POLICY IF EXISTS service_plans_provider ON public.service_plans;
CREATE POLICY service_plans_provider ON public.service_plans
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.services
            WHERE id = service_plans.service_id
            AND provider_account_id = public.get_current_account_id()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.services
            WHERE id = service_plans.service_id
            AND provider_account_id = public.get_current_account_id()
        )
    );

-- Tenants can see plans for subscribed services
DROP POLICY IF EXISTS service_plans_subscribed ON public.service_plans;
CREATE POLICY service_plans_subscribed ON public.service_plans
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.subscriptions sub
            JOIN public.services s ON s.id = sub.service_id
            WHERE s.id = service_plans.service_id
            AND sub.tenant_account_id = public.get_current_account_id()
        )
    );

----------------------------------------------------------------------------
-- SUBSCRIPTIONS POLICIES
----------------------------------------------------------------------------

-- Tenants can see their own subscriptions
DROP POLICY IF EXISTS subscriptions_tenant ON public.subscriptions;
CREATE POLICY subscriptions_tenant ON public.subscriptions
    FOR SELECT
    USING (tenant_account_id = public.get_current_account_id());

-- Providers can see subscriptions to their services
DROP POLICY IF EXISTS subscriptions_provider ON public.subscriptions;
CREATE POLICY subscriptions_provider ON public.subscriptions
    FOR SELECT
    USING (provider_account_id = public.get_current_account_id());

-- Tenants can create subscriptions for themselves
DROP POLICY IF EXISTS subscriptions_tenant_create ON public.subscriptions;
CREATE POLICY subscriptions_tenant_create ON public.subscriptions
    FOR INSERT
    WITH CHECK (
        tenant_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    );

-- Tenants can update their own subscriptions (cancel, etc.)
DROP POLICY IF EXISTS subscriptions_tenant_update ON public.subscriptions;
CREATE POLICY subscriptions_tenant_update ON public.subscriptions
    FOR UPDATE
    USING (
        tenant_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    )
    WITH CHECK (tenant_account_id = public.get_current_account_id());

-- Providers can update subscriptions to their services
DROP POLICY IF EXISTS subscriptions_provider_update ON public.subscriptions;
CREATE POLICY subscriptions_provider_update ON public.subscriptions
    FOR UPDATE
    USING (
        provider_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    )
    WITH CHECK (provider_account_id = public.get_current_account_id());

----------------------------------------------------------------------------
-- ACCOUNT_LINKS POLICIES
----------------------------------------------------------------------------

-- Users can see links involving their account
DROP POLICY IF EXISTS account_links_own ON public.account_links;
CREATE POLICY account_links_own ON public.account_links
    FOR SELECT
    USING (
        from_account_id = public.get_current_account_id()
        OR to_account_id = public.get_current_account_id()
    );

-- Admins can create links from their account
DROP POLICY IF EXISTS account_links_create ON public.account_links;
CREATE POLICY account_links_create ON public.account_links
    FOR INSERT
    WITH CHECK (
        from_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    );

-- Admins can delete links from their account
DROP POLICY IF EXISTS account_links_delete ON public.account_links;
CREATE POLICY account_links_delete ON public.account_links
    FOR DELETE
    USING (
        from_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    );

----------------------------------------------------------------------------
-- ENVIRONMENTS POLICIES
----------------------------------------------------------------------------

-- Users can see environments for their own account
DROP POLICY IF EXISTS environments_own ON public.environments;
CREATE POLICY environments_own ON public.environments
    FOR SELECT
    USING (account_id = public.get_current_account_id());

-- Admins can manage environments for their account
DROP POLICY IF EXISTS environments_admin ON public.environments;
CREATE POLICY environments_admin ON public.environments
    FOR ALL
    USING (
        account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    )
    WITH CHECK (account_id = public.get_current_account_id());

----------------------------------------------------------------------------
-- PROJECTS POLICIES (EXAMPLE TENANT-SCOPED TABLE)
----------------------------------------------------------------------------

-- Users can see projects in their tenant
DROP POLICY IF EXISTS projects_tenant ON public.projects;
CREATE POLICY projects_tenant ON public.projects
    FOR SELECT
    USING (tenant_account_id = public.get_current_account_id());

-- Users can create projects in their tenant
DROP POLICY IF EXISTS projects_create ON public.projects;
CREATE POLICY projects_create ON public.projects
    FOR INSERT
    WITH CHECK (
        tenant_account_id = public.get_current_account_id()
        AND created_by_user_id = public.get_current_user_id()
    );

-- Project creators and admins can update projects
DROP POLICY IF EXISTS projects_update ON public.projects;
CREATE POLICY projects_update ON public.projects
    FOR UPDATE
    USING (
        tenant_account_id = public.get_current_account_id()
        AND (
            created_by_user_id = public.get_current_user_id()
            OR public.is_current_user_admin()
        )
    )
    WITH CHECK (tenant_account_id = public.get_current_account_id());

-- Admins can delete projects in their tenant
DROP POLICY IF EXISTS projects_delete ON public.projects;
CREATE POLICY projects_delete ON public.projects
    FOR DELETE
    USING (
        tenant_account_id = public.get_current_account_id()
        AND public.is_current_user_admin()
    );

----------------------------------------------------------------------------
-- GRANT STATEMENTS FOR APPLICATION ROLES
----------------------------------------------------------------------------

-- Create application role if it doesn't exist
DO $$ BEGIN
    CREATE ROLE app_user;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO app_user;

-- Grant select on all tables to app_user (RLS will filter)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_user;

-- Grant specific DML permissions (RLS will enforce access)
GRANT INSERT, UPDATE, DELETE ON public.accounts TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.account_roles TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.users TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.services TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.service_plans TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.subscriptions TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.account_links TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.environments TO app_user;
GRANT INSERT, UPDATE, DELETE ON public.projects TO app_user;

-- Grant execute on helper functions
GRANT EXECUTE ON FUNCTION public.get_current_account_id() TO app_user;
GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO app_user;
GRANT EXECUTE ON FUNCTION public.is_current_user_admin() TO app_user;
GRANT EXECUTE ON FUNCTION public.account_is_provider(UUID) TO app_user;
GRANT EXECUTE ON FUNCTION public.can_access_account(UUID) TO app_user;

COMMIT;
