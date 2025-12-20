# Superset PostgreSQL-Native Production Makefile

# Export all environment variables to subprocesses
.EXPORT_ALL_VARIABLES:

# Load credentials from shell environment
# These should be set in ~/.zshrc
BASE_URL ?= https://superset.insightpulseai.net
SUPERSET_ADMIN_USER ?=
SUPERSET_ADMIN_PASS ?=
EXAMPLES_DB_URI ?=

.PHONY: help bootstrap validate ui-smoke end-to-end clean version digest \
        image-build image-scan image-push image-verify release-image \
        spec-validate agent-verify

help: ## Show this help message
	@echo "Superset PostgreSQL-Native Production - Available Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Required environment variables (set in ~/.zshrc):"
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

# =============================================================================
# Docker Image Build Targets
# =============================================================================

# Image configuration
IMAGE_REPO ?= ghcr.io/jgtolentino/ipai-superset
IMAGE_TAG ?= latest
PLATFORMS ?= linux/amd64,linux/arm64

image-build: ## Build multi-arch Docker image
	@echo "=== Building Docker Image ==="
	@IMAGE_REPO=$(IMAGE_REPO) IMAGE_TAG=$(IMAGE_TAG) PLATFORMS=$(PLATFORMS) \
		./skills/docker-image-build/scripts/build.sh $(ARGS)

image-scan: ## Scan Docker image for vulnerabilities
	@echo "=== Scanning Docker Image ==="
	@IMAGE_REPO=$(IMAGE_REPO) IMAGE_TAG=$(IMAGE_TAG) \
		./skills/docker-image-build/scripts/scan.sh $(ARGS)

image-push: ## Push Docker image to registry
	@echo "=== Pushing Docker Image ==="
	@IMAGE_REPO=$(IMAGE_REPO) IMAGE_TAG=$(IMAGE_TAG) \
		./skills/docker-image-build/scripts/push.sh $(ARGS)

image-verify: ## Verify Docker image
	@echo "=== Verifying Docker Image ==="
	@IMAGE_REPO=$(IMAGE_REPO) IMAGE_TAG=$(IMAGE_TAG) \
		./skills/docker-image-build/scripts/verify.sh $(ARGS)

release-image: ## Full release: build + scan + push + verify
	@echo "=== Full Image Release ==="
	@$(MAKE) image-build ARGS="--push"
	@$(MAKE) image-scan
	@$(MAKE) image-verify
	@echo "=== Release Complete ==="

# =============================================================================
# Agent and Spec Kit Targets
# =============================================================================

spec-validate: ## Validate all spec kits (constitution/prd/plan/tasks)
	@echo "=== Validating Spec Kits ==="
	@./scripts/spec_validate.sh

agent-verify: ## Run full agent verification (spec + repo health)
	@echo "=== Agent Verification ==="
	@./scripts/spec_validate.sh
	@echo ""
	@echo "Agent verification complete. Use /project:verify for full checks."
