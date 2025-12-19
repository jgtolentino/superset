# db-inventory (repo-wide datastore inventory)

Scans the repository recursively and inventories database/datastore connection references found in config, env files, code, manifests, and docs — **with secret redaction**.

## Run

```bash
python3 tools/db-inventory/inventory.py --root . --out tools/db-inventory/output
```

Outputs:

* `tools/db-inventory/output/db_inventory.json`
* `tools/db-inventory/output/db_inventory.csv`
* `tools/db-inventory/output/db_inventory.md`
* `tools/db-inventory/output/db_inventory_summary.md`

## Options

```bash
python3 tools/db-inventory/inventory.py --help
```

Common:

* `--exclude-dirs .git,node_modules,dist,build,.venv,__pycache__,.next`
* `--max-file-mb 5`
* `--format json,csv,md`

## Notes

* Offline scan only (no network).
* Secrets are redacted (passwords/tokens/keys and URL credentials).
* Partial findings are still recorded (e.g., host with no dbname).
