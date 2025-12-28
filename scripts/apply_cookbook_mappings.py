#!/usr/bin/env python3
"""Generate cookbook-to-hybrid mapping doc and ensure playbooks exist."""
from __future__ import annotations
from pathlib import Path
import yaml

MAP = Path("mappings/cookbook_to_hybrid.yaml")
OUT_MD = Path("catalog/adapted/COOKBOOK_TO_HYBRID_MAPPING.md")


def md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def format_source(source_list: list) -> str:
    """Format source list for display."""
    parts = []
    for item in source_list:
        if isinstance(item, dict):
            for k, v in item.items():
                parts.append(f"{k}:{v}")
        else:
            parts.append(str(item))
    return ", ".join(parts)


def main():
    cfg = yaml.safe_load(MAP.read_text("utf-8"))
    rows = cfg["mappings"]

    lines = []
    lines.append("# Cookbook to Hybrid Mapping (generated)\n")
    lines.append("This doc maps external best-practice sources to concrete modules, contracts, and checks in this repo.\n")

    lines.append("## Sources\n")
    for k, v in cfg["sources"].items():
        url = v.get("url") or v.get("site", "")
        lines.append(f"- **{k}**: {url}")
    lines.append("")

    lines.append("## Mapping Table\n")
    lines.append("| ID | Principle | Playbook | Hybrid Targets | Output Contracts | Checks |")
    lines.append("|---|---|---|---|---|---|")

    for r in rows:
        sources = format_source(r.get("source", []))
        targets = "<br>".join([md_escape(t) for t in r.get("hybrid_targets", [])])
        contracts = "<br>".join([md_escape(c) for c in r.get("output_contract", [])])
        checks = "<br>".join([md_escape(c) for c in r.get("checks", [])])
        lines.append(
            f'| `{r["id"]}` | {md_escape(r["principle"])}<br><sub>{md_escape(sources)}</sub> | `{r["playbook"]}` | {targets} | {contracts} | {checks} |'
        )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", "utf-8")
    print(f"Wrote {OUT_MD}")

    # Create stub playbooks if missing
    for r in rows:
        pb = Path(r["playbook"])
        pb.parent.mkdir(parents=True, exist_ok=True)
        if not pb.exists():
            pb.write_text(
                f"# {r['id']}\n\n"
                f"**Principle:** {r['principle']}\n\n"
                f"## Applies to\n" + "\n".join([f"- `{t}`" for t in r.get("hybrid_targets", [])]) + "\n\n"
                f"## Output contract\n" + "\n".join([f"- `{c}`" for c in r.get("output_contract", [])]) + "\n\n"
                f"## Checks\n" + "\n".join([f"- `{c}`" for c in r.get("checks", [])]) + "\n",
                "utf-8",
            )
            print(f"Created stub: {pb}")
        else:
            print(f"Playbook exists: {pb}")


if __name__ == "__main__":
    main()
