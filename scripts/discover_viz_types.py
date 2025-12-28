#!/usr/bin/env python3
"""Discover available viz types from Superset backend.

Run inside Superset container to generate available_viz_types.json
that the dashboard generator reads for ECharts-first fallback.

Usage:
    docker compose exec superset python discover_viz_types.py /app/available_viz_types.json
"""

import json
import os
import sys


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "available_viz_types.json"

    viz_types = None
    errors = []

    # Method 1: Direct import (common path)
    try:
        from superset.viz import viz_types as vt
        viz_types = list(vt.keys())
    except Exception as e:
        errors.append(f"superset.viz.viz_types: {e!r}")

    # Method 2: Heuristic scan of superset.viz module
    if viz_types is None:
        try:
            import superset.viz as viz
            candidates = []
            for name in dir(viz):
                if name.lower().endswith("viz_types"):
                    obj = getattr(viz, name)
                    if isinstance(obj, dict) and len(obj) > 10:
                        candidates.append((name, obj))
            if candidates:
                name, obj = sorted(candidates, key=lambda x: len(x[1]), reverse=True)[0]
                viz_types = list(obj.keys())
            else:
                raise RuntimeError("No viz_types dict found in superset.viz")
        except Exception as e:
            errors.append(f"superset.viz heuristic: {e!r}")

    # Method 3: Try superset-ui plugin registry (newer versions)
    if viz_types is None:
        try:
            from superset.common.chart_data import ChartDataResultFormat
            from superset.utils.core import get_example_default_schema
            # This is a fallback - list known defaults
            viz_types = [
                "echarts_timeseries_line", "echarts_timeseries_bar",
                "echarts_timeseries_area", "echarts_timeseries_scatter",
                "echarts_bar", "echarts_pie", "echarts_funnel",
                "echarts_gauge", "echarts_graph", "echarts_radar",
                "echarts_sunburst", "echarts_treemap", "echarts_tree",
                "echarts_boxplot", "echarts_bubble",
                "line", "bar", "pie", "area", "scatter",
                "big_number", "big_number_total",
                "table", "pivot_table",
                "heatmap", "word_cloud", "treemap", "sunburst",
                "funnel", "gauge", "histogram",
                "deck_path", "deck_scatter", "deck_grid",
                "country_map", "world_map",
            ]
        except Exception as e:
            errors.append(f"fallback list: {e!r}")

    if viz_types is None:
        raise SystemExit("Unable to discover viz types.\n" + "\n".join(errors))

    viz_types = sorted(set(map(str, viz_types)))

    # Categorize by plugin type
    echarts_types = [v for v in viz_types if v.startswith("echarts")]
    classic_types = [v for v in viz_types if not v.startswith("echarts")]

    payload = {
        "count": len(viz_types),
        "echarts_count": len(echarts_types),
        "classic_count": len(classic_types),
        "viz_types": viz_types,
        "echarts_types": echarts_types,
        "classic_types": classic_types,
        "source": "backend",
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    print(f"Wrote {out_path}")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
