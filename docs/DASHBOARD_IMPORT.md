# Dashboard Import Guide

This guide explains how to import dashboards into Superset from JSON files using the automated import script.

## Overview

The dashboard import script allows you to:
- Import dashboards from JSON files
- Bulk import multiple dashboards from a directory
- Automate dashboard deployment across environments
- Integrate with CI/CD pipelines

## Prerequisites

### Environment Variables

Set required credentials:

```bash
# In ~/.zshrc or .env
export BASE_URL="https://superset.example.com"
export SUPERSET_ADMIN_USER="your_admin_username"
export SUPERSET_ADMIN_PASS="your_admin_password"
```

### Python Requirements

The script uses only Python standard library (no external dependencies):
- `urllib.request` for HTTP requests
- `json` for JSON parsing
- `pathlib` for file operations

## Quick Start

### Import Single Dashboard

```bash
./scripts/import_dashboard.py examples/dashboards/sample_dashboard.json
```

Expected output:
```
=== Superset Dashboard Import ===
Base URL: https://superset.example.com
Path: examples/dashboards/sample_dashboard.json
🔐 Authenticating to Superset...
✅ Authentication successful

📊 Importing dashboard: sample_dashboard.json
✅ Dashboard imported successfully

=== Import Complete ===
```

### Import All Dashboards from Directory

```bash
./scripts/import_dashboard.py examples/dashboards/
```

Expected output:
```
=== Superset Dashboard Import ===
Base URL: https://superset.example.com
Path: examples/dashboards/

🔐 Authenticating to Superset...
✅ Authentication successful

📁 Found 3 dashboard file(s)

📊 Importing dashboard: dashboard1.json
✅ Dashboard imported successfully

📊 Importing dashboard: dashboard2.json
✅ Dashboard imported successfully

📊 Importing dashboard: dashboard3.json
✅ Dashboard imported successfully

=== Import Summary ===
✅ Successful: 3
❌ Failed: 0
📊 Total: 3
```

## Dashboard JSON Format

### Basic Structure

```json
{
  "dashboard_title": "My Dashboard",
  "description": "Dashboard description",
  "slug": "my-dashboard",
  "published": true,
  "css": "",
  "position_json": "{\"DASHBOARD_VERSION_KEY\":\"v2\"}",
  "metadata": {
    "filter_scopes": {},
    "expanded_slices": {},
    "refresh_frequency": 0,
    "default_filters": "{}",
    "color_scheme": "",
    "label_colors": {}
  },
  "slices": []
}
```

### With Charts

```json
{
  "dashboard_title": "Sales Dashboard",
  "slug": "sales-dashboard",
  "published": true,
  "slices": [
    {
      "slice_name": "Monthly Sales",
      "viz_type": "line",
      "params": {
        "datasource": "sales_data",
        "metrics": ["sum__amount"],
        "groupby": ["month"]
      }
    }
  ]
}
```

## Exporting Dashboards

### From Superset UI

1. Navigate to dashboard in Superset
2. Click three-dot menu (⋮)
3. Select "Export"
4. Save ZIP file
5. Extract JSON from ZIP
6. Place in `examples/dashboards/`

### Via API

```bash
# Get dashboard ID
DASHBOARD_ID=1

# Export dashboard
curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${BASE_URL}/api/v1/dashboard/export/?q=!(ids:!(${DASHBOARD_ID}))" \
  -o dashboard_${DASHBOARD_ID}.zip

# Extract JSON
unzip dashboard_${DASHBOARD_ID}.zip
```

## Advanced Usage

### Script Options

```bash
./scripts/import_dashboard.py --help
```

Output:
```
usage: import_dashboard.py [-h] [--skip-auth-check] path

Import Superset dashboards from JSON files

positional arguments:
  path               Path to dashboard JSON file or directory

optional arguments:
  -h, --help         show this help message and exit
  --skip-auth-check  Skip initial authentication check (not recommended)

Examples:
  # Import single dashboard
  import_dashboard.py dashboard.json
  
  # Import all dashboards from directory
  import_dashboard.py dashboards/
  
  # Import with explicit path
  import_dashboard.py /path/to/dashboard.json

Environment Variables (required):
  BASE_URL              Superset instance URL
  SUPERSET_ADMIN_USER   Admin username
  SUPERSET_ADMIN_PASS   Admin password
```

### Skip Authentication Check

For faster imports when credentials are known to be valid:

```bash
./scripts/import_dashboard.py --skip-auth-check examples/dashboards/
```

**Warning**: Only use this if you're certain credentials are correct.

## Integration Patterns

### CI/CD Pipeline

```yaml
# .github/workflows/deploy-dashboards.yml
name: Deploy Dashboards

on:
  push:
    branches: [ main ]
    paths:
      - 'examples/dashboards/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Import dashboards
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          SUPERSET_ADMIN_USER: ${{ secrets.SUPERSET_ADMIN_USER }}
          SUPERSET_ADMIN_PASS: ${{ secrets.SUPERSET_ADMIN_PASS }}
        run: |
          ./scripts/import_dashboard.py examples/dashboards/
```

### Makefile Integration

Add to `Makefile`:

```makefile
import-dashboards: ## Import all example dashboards
	@echo "=== Importing Dashboards ==="
	@./scripts/import_dashboard.py examples/dashboards/

import-dashboard: ## Import single dashboard (usage: make import-dashboard DASH=file.json)
	@echo "=== Importing Dashboard: $(DASH) ==="
	@./scripts/import_dashboard.py $(DASH)
```

Usage:
```bash
make import-dashboards
make import-dashboard DASH=examples/dashboards/sales.json
```

### Scheduled Imports

Using cron:

```bash
# Import dashboards daily at 2 AM
0 2 * * * cd /path/to/superset && ./scripts/import_dashboard.py examples/dashboards/
```

### n8n Workflow

See [N8N_INTEGRATION.md](N8N_INTEGRATION.md) for details on building n8n nodes for dashboard automation.

## Error Handling

### Common Errors

#### Missing Environment Variables

```
❌ BLOCKED: Missing required environment variables:
   - BASE_URL
   - SUPERSET_ADMIN_USER
   - SUPERSET_ADMIN_PASS
```

**Fix**: Set environment variables in `~/.zshrc` or export before running.

#### Authentication Failed

```
❌ Authentication failed (HTTP 401)
   Response: {"message": "Invalid login credentials"}
```

**Fix**: Verify credentials are correct and user has admin access.

#### Invalid JSON Format

```
❌ Invalid JSON in dashboard.json: Expecting property name enclosed in double quotes
```

**Fix**: Validate JSON syntax using `python3 -m json.tool dashboard.json`.

#### Dashboard Import Failed

```
❌ Import failed (HTTP 400)
   Response: {"message": "Invalid dashboard format"}
```

**Fix**: Ensure dashboard JSON matches Superset export format.

### Exit Codes

- `0`: Success
- `1`: Import failed or partial success
- `2`: Missing environment variables

## Best Practices

### 1. Validate JSON Before Import

```bash
# Check JSON syntax
python3 -m json.tool examples/dashboards/dashboard.json > /dev/null && echo "✅ Valid JSON"
```

### 2. Organize Dashboards by Environment

```
examples/dashboards/
├── production/
│   ├── sales_dashboard.json
│   └── analytics_dashboard.json
├── staging/
│   ├── test_dashboard.json
│   └── dev_dashboard.json
└── shared/
    └── common_metrics.json
```

Import specific environment:
```bash
./scripts/import_dashboard.py examples/dashboards/production/
```

### 3. Version Control Dashboard Changes

```bash
# Track dashboard changes in git
git add examples/dashboards/
git commit -m "Update sales dashboard with new metrics"
```

### 4. Test in Staging First

```bash
# Import to staging
export BASE_URL="https://staging.superset.example.com"
./scripts/import_dashboard.py examples/dashboards/

# Verify dashboards work

# Then import to production
export BASE_URL="https://superset.example.com"
./scripts/import_dashboard.py examples/dashboards/
```

### 5. Backup Existing Dashboards

Before bulk imports, export existing dashboards:

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Export all dashboards via API
# (See "Via API" section in Exporting Dashboards)
```

## Troubleshooting

### Script Can't Find Python

```bash
# Check Python installation
which python3

# If not found, install Python 3
# macOS: brew install python3
# Ubuntu: sudo apt-get install python3
```

### Permission Denied

```bash
chmod +x scripts/import_dashboard.py
```

### Connection Timeout

```
❌ Import error: <urlopen error timed out>
```

Check:
1. BASE_URL is correct and accessible
2. Network connectivity
3. Firewall rules allow connection

### Dataset Not Found

After import, dashboards may show "Dataset not found":

1. Ensure datasets exist in target Superset
2. Run bootstrap script first:
   ```bash
   ./scripts/bootstrap_examples_db.sh
   ```
3. Manually create missing datasets

## Testing

### Dry Run (Authentication Only)

```bash
# Test authentication without importing
python3 -c "
from scripts.import_dashboard import SupersetDashboardImporter, validate_environment
base_url, user, password = validate_environment()
importer = SupersetDashboardImporter(base_url, user, password)
print('✅ Authentication successful' if importer.authenticate() else '❌ Authentication failed')
"
```

### Validate Dashboard JSON

```python
#!/usr/bin/env python3
import json
import sys

def validate_dashboard(file_path):
    with open(file_path) as f:
        data = json.load(f)
    
    required = ['dashboard_title', 'slug', 'published']
    missing = [k for k in required if k not in data]
    
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False
    
    print("✅ Valid dashboard format")
    return True

if __name__ == '__main__':
    validate_dashboard(sys.argv[1])
```

## Resources

- [Superset REST API Documentation](https://superset.apache.org/docs/api)
- [Example Dashboard Files](../examples/dashboards/)
- [n8n Integration Guide](N8N_INTEGRATION.md)

## Support

For issues or questions:
- Check troubleshooting section above
- Review example dashboards in `examples/dashboards/`
- Open issue in repository: https://github.com/jgtolentino/superset
