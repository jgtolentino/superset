# Example Dashboards

This directory contains sample dashboard JSON files that can be imported into Superset.

## Structure

Dashboard JSON files should follow the Superset export format with these key fields:

```json
{
  "dashboard_title": "Dashboard Name",
  "description": "Dashboard description",
  "slug": "dashboard-slug",
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

## Usage

### Import Single Dashboard

```bash
./scripts/import_dashboard.py examples/dashboards/sample_dashboard.json
```

### Import All Dashboards

```bash
./scripts/import_dashboard.py examples/dashboards/
```

## Exporting Dashboards

To export a dashboard from Superset for use as a template:

1. Navigate to the dashboard in Superset UI
2. Click the three-dot menu (⋮)
3. Select "Export"
4. Save the ZIP file and extract the JSON
5. Place the JSON file in this directory

## Notes

- Dashboard imports require authentication via environment variables
- See main README.md for required environment variables
- Imported dashboards may need dataset connections to be reconfigured
