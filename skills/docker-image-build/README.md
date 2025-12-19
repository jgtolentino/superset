# Docker Image Build Skill

Multi-architecture Docker image build, scan, and push automation for Superset.

## Features

- Multi-platform builds (linux/amd64, linux/arm64) via `docker buildx`
- Security scanning with Docker Scout (preferred) or Trivy (fallback)
- OCI-compliant image labels
- GHCR (GitHub Container Registry) integration
- Verification checks for built images

## Quick Start

```bash
# Build image (local load, single platform)
make image-build IMAGE_TAG=dev --load

# Build multi-arch (no local load)
make image-build IMAGE_TAG=v1.0.0

# Scan for vulnerabilities
make image-scan IMAGE_TAG=dev

# Push to GHCR
export GITHUB_TOKEN="your_token"
make image-push IMAGE_TAG=v1.0.0

# Verify image
make image-verify IMAGE_TAG=dev

# Full release (build + scan + push + verify)
make release-image IMAGE_TAG=v1.0.0
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_REPO` | `ghcr.io/jgtolentino/ipai-superset` | Image repository |
| `IMAGE_TAG` | `latest` | Image tag |
| `PLATFORMS` | `linux/amd64,linux/arm64` | Target platforms |
| `DOCKERFILE` | `Dockerfile` | Dockerfile path |
| `BUILD_CONTEXT` | `.` | Build context directory |
| `GITHUB_TOKEN` | - | Token for GHCR push |
| `SECURITY_OUTPUT_DIR` | `tools/security/output` | Scan results directory |

## Scripts

### `scripts/build.sh`

Builds multi-architecture Docker images using buildx.

```bash
# Build and load locally (single platform)
./skills/docker-image-build/scripts/build.sh --load

# Build and push directly
./skills/docker-image-build/scripts/build.sh --push
```

### `scripts/scan.sh`

Scans images for vulnerabilities. Uses Docker Scout if available, falls back to Trivy.

```bash
# Table output
./skills/docker-image-build/scripts/scan.sh

# JSON output
./skills/docker-image-build/scripts/scan.sh --format json

# SARIF output (for GitHub Security tab)
./skills/docker-image-build/scripts/scan.sh --format sarif

# Filter severity
./skills/docker-image-build/scripts/scan.sh --severity critical,high
```

Output files are written to `tools/security/output/`:
- `scout-results.json` or `trivy-results.json`
- `scout-results.sarif` or `trivy-results.sarif`

### `scripts/push.sh`

Pushes image to container registry.

```bash
# Push to GHCR
export GITHUB_TOKEN="ghp_xxx"
./skills/docker-image-build/scripts/push.sh

# Dry run
./skills/docker-image-build/scripts/push.sh --dry-run
```

### `scripts/verify.sh`

Verifies image integrity and functionality.

```bash
# Full verification
./skills/docker-image-build/scripts/verify.sh

# Quick check (image exists + history only)
./skills/docker-image-build/scripts/verify.sh --quick
```

Checks performed:
1. Image exists locally
2. Docker history available
3. `superset --version` returns output (or Python fallback)
4. Image size reported
5. OCI labels present

## CI/CD Integration

See `.github/workflows/image-build-scan.yml` for automated:
- Build on push to main
- Build (no push) on PRs
- Vulnerability scanning with SARIF upload
- Buildx layer caching

## Makefile Targets

```bash
make image-build    # Build multi-arch image
make image-scan     # Scan for vulnerabilities
make image-push     # Push to registry
make image-verify   # Verify image
make release-image  # Full release workflow
```

## Troubleshooting

### "buildx not available"

```bash
docker buildx install
docker buildx create --use
```

### "Scanner not found"

Install Docker Scout:
```bash
docker scout --help  # Built into Docker Desktop
```

Or install Trivy:
```bash
brew install trivy  # macOS
apt-get install trivy  # Ubuntu
```

### "GHCR push denied"

```bash
# Create PAT with write:packages scope
export GITHUB_TOKEN="ghp_xxx"
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```
