-- Migration: 002_create_multi_tenant_provider_schema.sql
-- Description: Creates the multi-tenant provider model schema
-- Author: InsightPulse AI
-- Date: 2026-01-13
--
-- This schema implements a flexible multi-tenant model where:
--   - Tenant = organization using the platform
--   - Provider = organization offering services/agents to other tenants
--   - The same org can be BOTH tenant and provider
--
-- Core concepts:
--   - accounts: Companies/orgs (TBWA, client brands, InsightPulseAI, etc.)
--   - account_roles: TENANT, PROVIDER, INTERNAL roles per account
--   - services: Things a provider offers (AI agents, dashboards, etc.)
--   - subscriptions: Links tenant accounts to provider services
--   - account_links: Explicit relationships (Provider of, Reseller of, etc.)
--   - environments: Maps tenants to infra (Supabase/Vercel/DO IDs)

BEGIN;

-- Record migration
INSERT INTO public.schema_migrations (version) VALUES ('002_create_multi_tenant_provider_schema')
ON CONFLICT (version) DO NOTHING;

----------------------------------------------------------------------------
-- ENUMS
----------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE account_role_type AS ENUM ('TENANT', 'PROVIDER', 'INTERNAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('DRAFT', 'ACTIVE', 'SUSPENDED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE environment_type AS ENUM ('DEV', 'STAGING', 'PROD');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE account_link_type AS ENUM ('PROVIDER_OF', 'RESELLER_OF', 'PARTNER_OF');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

----------------------------------------------------------------------------
-- CORE ENTITIES
----------------------------------------------------------------------------

-- accounts: Represents both tenants and providers
-- Roles live in account_roles table
CREATE TABLE IF NOT EXISTS public.accounts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                TEXT NOT NULL UNIQUE,           -- human-readable handle
    name                TEXT NOT NULL,
    legal_name          TEXT,
    country             TEXT,
    timezone            TEXT DEFAULT 'UTC',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- Multi-tenancy hints
    default_locale      TEXT DEFAULT 'en',
    billing_email       TEXT,

    -- Metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- account_roles: Defines what roles an account has
-- An account can have multiple roles (e.g., both TENANT and PROVIDER)
CREATE TABLE IF NOT EXISTS public.account_roles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    role                account_role_type NOT NULL,
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (account_id, role)
);

-- users: Users belong to one primary account
CREATE TABLE IF NOT EXISTS public.users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    email               TEXT NOT NULL UNIQUE,
    full_name           TEXT,
    is_admin            BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- Optional external IDs for integration
    auth_user_id        UUID,               -- Supabase auth.users.id
    odoo_user_id        INTEGER,            -- res_users.id mapping
    superset_user_id    INTEGER,            -- Superset ab_user.id

    -- Metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

----------------------------------------------------------------------------
-- PROVIDER SIDE: SERVICES & PLANS
----------------------------------------------------------------------------

-- services: Things a provider offers (AI agents, dashboards, integrations, etc.)
CREATE TABLE IF NOT EXISTS public.services (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_account_id         UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    key                         TEXT NOT NULL UNIQUE,       -- e.g., "scout-dashboard", "ask-copilot"
    name                        TEXT NOT NULL,
    description                 TEXT,
    is_public                   BOOLEAN NOT NULL DEFAULT FALSE,

    -- Optional technical hints
    category                    TEXT,                       -- "AI_AGENT", "DASHBOARD", "ERP_INTEGRATION"
    default_environment_type    environment_type,

    -- Metadata
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- service_plans: Pricing tiers for services
CREATE TABLE IF NOT EXISTS public.service_plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id          UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,
    key                 TEXT NOT NULL,              -- "free", "pro", "enterprise"
    name                TEXT NOT NULL,
    description         TEXT,
    monthly_price_cents INTEGER DEFAULT 0,          -- 0 for free
    max_seats           INTEGER,

    -- Feature flags stored as JSONB
    features            JSONB DEFAULT '{}',

    -- Metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (service_id, key)
);

----------------------------------------------------------------------------
-- TENANT SIDE: SUBSCRIPTIONS & RELATIONSHIPS
----------------------------------------------------------------------------

-- subscriptions: Links tenant accounts to provider services
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_account_id       UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    provider_account_id     UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    service_id              UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,
    service_plan_id         UUID REFERENCES public.service_plans(id) ON DELETE SET NULL,
    status                  subscription_status NOT NULL DEFAULT 'DRAFT',

    -- Subscription lifecycle
    started_at              TIMESTAMPTZ,
    ended_at                TIMESTAMPTZ,
    trial_ends_at           TIMESTAMPTZ,

    -- Optional billing / external references
    external_ref            TEXT,               -- Stripe subscription ID, invoice ID, etc.

    -- Metadata
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- account_links: Explicit relationships between accounts
-- For PROVIDER_OF: from_account is provider, to_account is tenant
CREATE TABLE IF NOT EXISTS public.account_links (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_account_id     UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    to_account_id       UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    link_type           account_link_type NOT NULL,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (from_account_id, to_account_id, link_type),

    -- Prevent self-referencing
    CONSTRAINT no_self_link CHECK (from_account_id != to_account_id)
);

----------------------------------------------------------------------------
-- ENVIRONMENTS (SUPABASE / VERCEL / DO BINDINGS)
----------------------------------------------------------------------------

-- environments: Maps accounts to infrastructure
CREATE TABLE IF NOT EXISTS public.environments (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id              UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    env_type                environment_type NOT NULL,

    -- Infrastructure bindings
    supabase_project_ref    TEXT,               -- e.g., "cxzllzyxwpyptfretryc"
    vercel_project_id       TEXT,
    digitalocean_app_id     TEXT,
    odoo_db_name            TEXT,               -- if mapping per tenant / db
    superset_database_key   TEXT,               -- logical DB name in Superset

    -- Connection details (encrypted at rest)
    connection_string       TEXT,               -- encrypted connection string
    api_key                 TEXT,               -- encrypted API key

    -- Metadata
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (account_id, env_type)
);

----------------------------------------------------------------------------
-- EXAMPLE APP-SCOPED TABLE (ROW-BASED MULTI-TENANCY)
----------------------------------------------------------------------------

-- projects: Example of a tenant-scoped entity
CREATE TABLE IF NOT EXISTS public.projects (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_account_id   UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    key                 TEXT NOT NULL,          -- short code
    status              TEXT NOT NULL DEFAULT 'active',
    created_by_user_id  UUID NOT NULL REFERENCES public.users(id) ON DELETE SET NULL,

    -- Metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_account_id, key)
);

----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
----------------------------------------------------------------------------

-- Account lookups
CREATE INDEX IF NOT EXISTS idx_accounts_slug ON public.accounts(slug);
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON public.accounts(is_active);

-- Account roles
CREATE INDEX IF NOT EXISTS idx_account_roles_account_id ON public.account_roles(account_id);
CREATE INDEX IF NOT EXISTS idx_account_roles_role ON public.account_roles(role);

-- Users
CREATE INDEX IF NOT EXISTS idx_users_account_id ON public.users(account_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON public.users(auth_user_id);

-- Services
CREATE INDEX IF NOT EXISTS idx_services_provider_account_id ON public.services(provider_account_id);
CREATE INDEX IF NOT EXISTS idx_services_key ON public.services(key);
CREATE INDEX IF NOT EXISTS idx_services_category ON public.services(category);
CREATE INDEX IF NOT EXISTS idx_services_is_public ON public.services(is_public);

-- Service plans
CREATE INDEX IF NOT EXISTS idx_service_plans_service_id ON public.service_plans(service_id);

-- Subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant_account_id ON public.subscriptions(tenant_account_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_provider_account_id ON public.subscriptions(provider_account_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_service_id ON public.subscriptions(service_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant_service ON public.subscriptions(tenant_account_id, service_id);

-- Account links
CREATE INDEX IF NOT EXISTS idx_account_links_from_account ON public.account_links(from_account_id);
CREATE INDEX IF NOT EXISTS idx_account_links_to_account ON public.account_links(to_account_id);
CREATE INDEX IF NOT EXISTS idx_account_links_type ON public.account_links(link_type);

-- Environments
CREATE INDEX IF NOT EXISTS idx_environments_account_id ON public.environments(account_id);
CREATE INDEX IF NOT EXISTS idx_environments_env_type ON public.environments(env_type);

-- Projects (tenant-scoped)
CREATE INDEX IF NOT EXISTS idx_projects_tenant_account_id ON public.projects(tenant_account_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);

----------------------------------------------------------------------------
-- TRIGGER FUNCTION FOR updated_at
----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with updated_at column
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT table_name FROM information_schema.columns
             WHERE table_schema = 'public'
             AND column_name = 'updated_at'
             AND table_name IN ('accounts', 'users', 'services', 'service_plans', 'subscriptions', 'environments', 'projects')
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trigger_update_%s_updated_at ON public.%s;
            CREATE TRIGGER trigger_update_%s_updated_at
                BEFORE UPDATE ON public.%s
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$;

----------------------------------------------------------------------------
-- VIEWS FOR COMMON QUERIES
----------------------------------------------------------------------------

-- View: Active provider accounts with their services
CREATE OR REPLACE VIEW public.v_providers AS
SELECT
    a.id AS account_id,
    a.slug,
    a.name,
    a.is_active,
    COUNT(DISTINCT s.id) AS service_count,
    COUNT(DISTINCT sub.id) AS subscription_count
FROM public.accounts a
JOIN public.account_roles ar ON ar.account_id = a.id AND ar.role = 'PROVIDER'
LEFT JOIN public.services s ON s.provider_account_id = a.id
LEFT JOIN public.subscriptions sub ON sub.provider_account_id = a.id AND sub.status = 'ACTIVE'
WHERE a.is_active = TRUE
GROUP BY a.id, a.slug, a.name, a.is_active;

-- View: Active tenant accounts with their subscriptions
CREATE OR REPLACE VIEW public.v_tenants AS
SELECT
    a.id AS account_id,
    a.slug,
    a.name,
    a.is_active,
    COUNT(DISTINCT sub.id) AS active_subscription_count
FROM public.accounts a
JOIN public.account_roles ar ON ar.account_id = a.id AND ar.role = 'TENANT'
LEFT JOIN public.subscriptions sub ON sub.tenant_account_id = a.id AND sub.status = 'ACTIVE'
WHERE a.is_active = TRUE
GROUP BY a.id, a.slug, a.name, a.is_active;

-- View: Full subscription details
CREATE OR REPLACE VIEW public.v_subscription_details AS
SELECT
    sub.id AS subscription_id,
    sub.status,
    sub.started_at,
    sub.ended_at,
    sub.trial_ends_at,
    ta.id AS tenant_id,
    ta.slug AS tenant_slug,
    ta.name AS tenant_name,
    pa.id AS provider_id,
    pa.slug AS provider_slug,
    pa.name AS provider_name,
    s.id AS service_id,
    s.key AS service_key,
    s.name AS service_name,
    sp.id AS plan_id,
    sp.key AS plan_key,
    sp.name AS plan_name,
    sp.monthly_price_cents
FROM public.subscriptions sub
JOIN public.accounts ta ON ta.id = sub.tenant_account_id
JOIN public.accounts pa ON pa.id = sub.provider_account_id
JOIN public.services s ON s.id = sub.service_id
LEFT JOIN public.service_plans sp ON sp.id = sub.service_plan_id;

COMMIT;
