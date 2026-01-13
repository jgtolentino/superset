# Multi-Tenant Provider Model

A flexible multi-tenant architecture where organizations can be both **tenants** (consumers) and **providers** (service/agent vendors) simultaneously.

## Overview

### Core Concepts

| Entity | Description |
|--------|-------------|
| **Account** | Organization/company (e.g., TBWA, InsightPulseAI, client brands) |
| **Account Role** | TENANT, PROVIDER, or INTERNAL - same account can have multiple roles |
| **User** | Belongs to one primary account |
| **Service** | Something a provider offers (AI agents, dashboards, integrations) |
| **Service Plan** | Pricing tier for a service (free, pro, enterprise) |
| **Subscription** | Links a tenant to a provider's service |
| **Account Link** | Explicit relationship between accounts (provider-of, reseller, partner) |
| **Environment** | Infrastructure binding (Supabase, Vercel, DigitalOcean mappings) |

### Entity Relationship

```
accounts 1──N account_roles (defines TENANT/PROVIDER/INTERNAL)
accounts 1──N users
accounts 1──N services (as providers)
accounts 1──N subscriptions (as tenants)
accounts N──N accounts via account_links
accounts 1──N environments
services 1──N service_plans
services 1──N subscriptions
```

## Files

| File | Purpose |
|------|---------|
| `schema.dbml` | DBML schema for visualization (use [dbdiagram.io](https://dbdiagram.io)) |
| `schema.prisma` | Prisma ORM schema for TypeScript/Node.js |
| `../../db/migrations/002_create_multi_tenant_provider_schema.sql` | PostgreSQL migration |
| `../../db/migrations/003_create_rls_policies.sql` | Row-Level Security policies |

## Quick Start

### 1. Apply Migrations

```bash
# Connect to your PostgreSQL database
psql $SUPERSET__SQLALCHEMY_DATABASE_URI

# Apply migrations in order
\i db/migrations/001_create_examples_schema.sql
\i db/migrations/002_create_multi_tenant_provider_schema.sql
\i db/migrations/003_create_rls_policies.sql
```

### 2. Using with Prisma

```bash
# Copy schema to your project
cp spec/multi-tenant-model/schema.prisma ./prisma/schema.prisma

# Set DATABASE_URL in your .env
echo "DATABASE_URL=postgresql://user:pass@host:5432/db" >> .env

# Generate client
npx prisma generate

# Or run migrations (if starting fresh)
npx prisma migrate dev --name init
```

### 3. Setting Up RLS Context

Before querying, set the session context:

```sql
-- Set current account and user for RLS
SET app.current_account_id = 'your-account-uuid';
SET app.current_user_id = 'your-user-uuid';
```

Or in application code:

```typescript
// Before each request, set the tenant context
await prisma.$executeRaw`SET app.current_account_id = ${accountId}`;
await prisma.$executeRaw`SET app.current_user_id = ${userId}`;
```

## Usage Examples

### Create an Account with Roles

```typescript
// Create a new account that is both tenant and provider
const account = await prisma.account.create({
  data: {
    slug: 'acme-corp',
    name: 'Acme Corporation',
    legalName: 'Acme Corp LLC',
    country: 'US',
    timezone: 'America/New_York',
    roles: {
      create: [
        { role: 'TENANT', isPrimary: true },
        { role: 'PROVIDER' }
      ]
    }
  },
  include: { roles: true }
});
```

### Create a User

```typescript
const user = await prisma.user.create({
  data: {
    accountId: account.id,
    email: 'admin@acme.com',
    fullName: 'Admin User',
    isAdmin: true
  }
});
```

### Provider: Create a Service with Plans

```typescript
const service = await prisma.service.create({
  data: {
    providerAccountId: account.id,
    key: 'ask-copilot',
    name: 'Ask Copilot AI Agent',
    description: 'AI-powered analytics assistant',
    category: 'AI_AGENT',
    isPublic: true,
    plans: {
      create: [
        {
          key: 'free',
          name: 'Free Tier',
          monthlyPriceCents: 0,
          maxSeats: 3,
          features: { queries: 100, history: '7d' }
        },
        {
          key: 'pro',
          name: 'Pro',
          monthlyPriceCents: 4900,
          maxSeats: 10,
          features: { queries: 10000, history: '90d', priority: true }
        }
      ]
    }
  },
  include: { plans: true }
});
```

### Tenant: Subscribe to a Service

```typescript
const subscription = await prisma.subscription.create({
  data: {
    tenantAccountId: tenantAccount.id,
    providerAccountId: providerAccount.id,
    serviceId: service.id,
    servicePlanId: proPlan.id,
    status: 'ACTIVE',
    startedAt: new Date(),
    trialEndsAt: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000) // 14 days
  }
});
```

### Create Account Link (Provider Relationship)

```typescript
const link = await prisma.accountLink.create({
  data: {
    fromAccountId: providerAccount.id,
    toAccountId: tenantAccount.id,
    linkType: 'PROVIDER_OF',
    metadata: { contract: 'ENT-2026-001', startDate: '2026-01-01' }
  }
});
```

### Query with Multi-Tenant Context

```typescript
// Get all services available to current tenant
const availableServices = await prisma.service.findMany({
  where: {
    OR: [
      { isPublic: true },
      {
        subscriptions: {
          some: {
            tenantAccountId: currentAccountId,
            status: 'ACTIVE'
          }
        }
      }
    ]
  },
  include: { plans: true }
});

// Get tenant's active subscriptions
const subscriptions = await prisma.subscription.findMany({
  where: {
    tenantAccountId: currentAccountId,
    status: 'ACTIVE'
  },
  include: {
    service: true,
    servicePlan: true,
    providerAccount: true
  }
});
```

## Tenant-Scoped Tables

All domain tables should follow this pattern:

```prisma
model YourDomainEntity {
  id              String @id @default(uuid())
  tenantAccountId String @map("tenant_account_id")
  // ... your fields

  tenantAccount Account @relation(fields: [tenantAccountId], references: [id])

  @@map("your_domain_entities")
}
```

Then add RLS policy in SQL:

```sql
ALTER TABLE public.your_domain_entities ENABLE ROW LEVEL SECURITY;

CREATE POLICY your_entities_tenant ON public.your_domain_entities
    FOR ALL
    USING (tenant_account_id = public.get_current_account_id())
    WITH CHECK (tenant_account_id = public.get_current_account_id());
```

## Odoo Integration

The model maps to Odoo CE/OCA as follows:

| Multi-Tenant Model | Odoo Model |
|--------------------|------------|
| `accounts` | `res.company` |
| `users` | `res.users` |
| `users.odoo_user_id` | FK to `res.users.id` |
| `environments.odoo_db_name` | Per-tenant Odoo database name |

For multi-company Odoo deployments, use `company_id` field for tenant isolation.

## Supabase Integration

1. **Auth Integration**: Map `users.auth_user_id` to `auth.users.id`
2. **RLS**: Use `auth.uid()` in policies instead of session variables
3. **JWT Claims**: Add `account_id` to JWT for automatic tenant context

Example Supabase RLS policy:

```sql
CREATE POLICY tenant_isolation ON public.projects
    FOR ALL
    USING (tenant_account_id = (auth.jwt() ->> 'account_id')::UUID);
```

## Views

The schema includes helper views:

- `v_providers` - Active providers with service/subscription counts
- `v_tenants` - Active tenants with subscription counts
- `v_subscription_details` - Full subscription info with joined data

## Security Considerations

1. **Never expose** `connection_string` or `api_key` fields to clients
2. **Always set** RLS context before queries
3. **Validate** account ownership before creating subscriptions
4. **Audit** account link creation (provider relationships)
5. **Encrypt** sensitive environment fields at rest

## License

Apache 2.0 - InsightPulse AI
