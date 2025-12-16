# Superset PostgreSQL-Native Production Makefile

# Export all environment variables to subprocesses
.EXPORT_ALL_VARIABLES:

# Load credentials from shell environment
# These should be set in .env (gitignored) or exported
BASE_URL ?= https://superset.insightpulseai.net
SUPERSET_ADMIN_USER ?=
SUPERSET_ADMIN_PASS ?=
EXAMPLES_DB_URI ?=

.PHONY: help bootstrap validate ui-smoke end-to-end clean version digest deploy

help: ## Show this help message
	@echo "Superset PostgreSQL-Native Production - Available Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Required environment variables (set in .env or export):"
	@echo "  - SUPERSET_ADMIN_USER"
	@echo "  - SUPERSET_ADMIN_PASS"
	@echo "  - EXAMPLES_DB_URI"
	@echo "  - BASE_URL (optional, defaults to https://superset.insightpulseai.net)"

bootstrap: ## Bootstrap Superset with Examples (Postgres) database and datasets
	@echo "=== Running Bootstrap Script ==="
	@./scripts/bootstrap_examples_db.sh

validate: ## Run comprehensive validation suite (7 checks)
	@echo "=== Running Validation Suite ==="
	@./scripts/validate.sh

ui-smoke: ## Run Playwright UI smoke tests
	@echo "=== Running Playwright Smoke Tests ==="
	@command -v npx >/dev/null 2>&1 || { echo "Error: Node.js/npm not installed"; exit 1; }
	@npx playwright install chromium --quiet 2>/dev/null || true
	@npx playwright test playwright/smoke.spec.ts

end-to-end: ## Run end-to-end proof suite (datasets API + SQL + UI)
	@echo "=== Running End-to-End Proof Suite ==="
	@./scripts/end_to_end_proof.sh

load-samples: ## Load official Superset sample dashboards into production
	@echo "=== Loading Official Superset Samples ==="
	@./scripts/load_official_samples.sh

clean: ## Clean up artifacts directory
	@echo "=== Cleaning artifacts ==="
	@rm -rf artifacts/*.png
	@echo "✅ Artifacts cleaned"

version: ## Get running Superset version (authenticated API)
	@echo "=== Getting Superset Version ==="
	@./scripts/get_superset_version.sh

digest: ## Get image digest for pinning (default: 4.1.1)
	@echo "=== Getting Image Digest ==="
	@./scripts/get_image_digest.sh $(or $(TAG),4.1.1)

APP_ID ?= 73af11cb-dab2-4cb1-9770-291c536531e6

deploy: ## Deploy pinned image to DO App Platform (requires doctl)
	@echo "=== Deploying to DigitalOcean App Platform ==="
	@command -v doctl >/dev/null 2>&1 || { echo "Error: doctl not installed"; exit 1; }
	@echo "Step 1: Updating app spec with --update-sources..."
	doctl apps update $(APP_ID) --spec infra/do/superset-app.yaml --update-sources
	@echo ""
	@echo "Step 2: Creating deployment to trigger image pull..."
	doctl apps create-deployment $(APP_ID)
	@echo ""
	@echo "Step 3: Checking deployment status..."
	doctl apps list-deployments $(APP_ID) | head -10
	@echo ""
	@echo "✅ Deployment triggered. Monitor with: doctl apps list-deployments $(APP_ID)"
