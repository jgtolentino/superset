# Superset PostgreSQL-Native Production Makefile

.PHONY: help bootstrap validate ui-smoke end-to-end clean

help: ## Show this help message
	@echo "Superset PostgreSQL-Native Production - Available Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Bootstrap Superset with Examples (Postgres) database and datasets
	@echo "=== Running Bootstrap Script ==="
	./scripts/bootstrap_examples_db.sh

validate: ## Run comprehensive validation suite (7 checks)
	@echo "=== Running Validation Suite ==="
	./scripts/validate.sh

ui-smoke: ## Run Playwright UI smoke tests
	@echo "=== Running Playwright Smoke Tests ==="
	@command -v npx >/dev/null 2>&1 || { echo "Error: Node.js/npm not installed"; exit 1; }
	@npx playwright install chromium --quiet 2>/dev/null || true
	npx playwright test playwright/smoke.spec.ts

end-to-end: ## Run end-to-end proof suite (datasets API + SQL + UI)
	@echo "=== Running End-to-End Proof Suite ==="
	./scripts/end_to_end_proof.sh

clean: ## Clean up artifacts directory
	@echo "=== Cleaning artifacts ==="
	rm -rf artifacts/*.png
	@echo "✅ Artifacts cleaned"
