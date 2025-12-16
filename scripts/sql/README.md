# Superset Example Datasets - PostgreSQL SQL Scripts

This directory contains SQL scripts to create all example datasets for Apache Superset dashboards.

## Datasets Created

### Messaging & Collaboration (002)
| Table | Type | Description |
|-------|------|-------------|
| `users` | Physical | User accounts |
| `channels` | Physical | Communication channels |
| `channel_members` | Physical | Channel membership junction |
| `users_channels` | Physical | User-channel relationships |
| `threads` | Physical | Discussion threads |
| `messages` | Physical | Chat messages |

### Analytics & Sales (003)
| Table | Type | Description |
|-------|------|-------------|
| `cleaned_sales_data` | Physical | Retail sales transactions |
| `video_game_sales` | Physical | Video game sales by platform |
| `exported_stats` | Physical | Generic metrics export |
| `FCC 2018 Survey` | Physical | Developer survey data |
| `unicode_test` | Physical | Internationalization test data |

### Geographic & Demographics (004)
| Table | Type | Description |
|-------|------|-------------|
| `flights` | Physical | US flight data |
| `birth_names` | Physical | US baby names by state |
| `birth_france_by_region` | Physical | French births by region |
| `long_lat` | Physical | City coordinates |
| `bart_lines` | Physical | SF BART transit lines |
| `sf_population_polygons` | Physical | SF neighborhood demographics |
| `covid_vaccines` | Physical | COVID vaccination data |
| `wb_health_population` | Physical | World Bank health metrics |

### Virtual Datasets / Views (005)
| View | Description |
|------|-------------|
| `v_users_channels` | Users with channel memberships |
| `v_messages_channels` | Messages with channel context |
| `v_new_members_daily` | Daily new member signups |
| `v_members_channels_2` | Channel analytics |
| `hierarchical_dataset` | Hierarchical data for treemaps |

## Installation

### Option 1: Supabase SQL Editor (Recommended)

1. Go to your Supabase Dashboard → SQL Editor
2. Execute each file in order:
   ```
   001_create_schema.sql
   002_messaging_tables.sql
   003_analytics_tables.sql
   004_geographic_tables.sql
   005_views.sql
   006_sample_data.sql
   ```

### Option 2: Using psql

```bash
# Set your Supabase connection string
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Run all scripts
cd scripts/sql
psql "$DATABASE_URL" -f 001_create_schema.sql
psql "$DATABASE_URL" -f 002_messaging_tables.sql
psql "$DATABASE_URL" -f 003_analytics_tables.sql
psql "$DATABASE_URL" -f 004_geographic_tables.sql
psql "$DATABASE_URL" -f 005_views.sql
psql "$DATABASE_URL" -f 006_sample_data.sql
```

### Option 3: Combined Script

```bash
# Using psql with the master script
cd scripts/sql
psql "$DATABASE_URL" -f run_all.sql
```

## Connecting to Superset

After running the SQL scripts, configure Superset to connect to your database:

1. **Database Connection**:
   - SQLAlchemy URI: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - Database Name: `Examples (Postgres)`

2. **Schema Configuration**:
   - Add `examples` to the allowed schemas
   - Enable schema browsing

3. **Dataset Registration**:
   - Go to Data → Datasets → + Dataset
   - Select database, schema (`examples`), and table
   - Repeat for each table you want to visualize

## Schema Structure

```
postgres/
├── examples/          # Main schema for example datasets
│   ├── users
│   ├── channels
│   ├── messages
│   ├── flights
│   ├── birth_names
│   └── ... (all other tables)
└── public/
    └── hierarchical_dataset  # View for treemap visualizations
```

## Permissions

The scripts grant access to Supabase default roles:
- `anon` - Anonymous access
- `authenticated` - Authenticated users
- `service_role` - Service role access

## Customization

Feel free to modify the sample data in `006_sample_data.sql` or add your own data after the tables are created.
