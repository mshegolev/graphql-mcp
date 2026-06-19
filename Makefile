.PHONY: release patch minor major check-pipeline

# Default release - asks for version bump type
release:
	@echo "Running auto-release workflow..."
	./scripts/auto-release.sh

# Patch version bump (0.0.x)
patch:
	@echo "Creating patch release..."
	./scripts/auto-release.sh <<< "1"

# Minor version bump (0.x.0)
minor:
	@echo "Creating minor release..."
	./scripts/auto-release.sh <<< "2"

# Major version bump (x.0.0)
major:
	@echo "Creating major release..."
	./scripts/auto-release.sh <<< "3"

# Check CI pipeline status
check-pipeline:
	@echo "Checking CI pipeline status..."
	gh api repos/mshegolev/graphql-mcp/actions/workflows/ci.yml/runs --jq '.workflow_runs[0] | "Status: \(.status), Conclusion: \(.conclusion)"' 2>/dev/null || echo "Could not fetch pipeline status"

# Install dependencies for the release script
install-deps:
	pip install setuptools_scm

# Help
help:
	@echo "Available commands:"
	@echo "  make release     - Run interactive release workflow"
	@echo "  make patch       - Create patch release (0.0.x)"
	@echo "  make minor       - Create minor release (0.x.0)"
	@echo "  make major       - Create major release (x.0.0)"
	@echo "  make check-pipeline - Check CI pipeline status"
	@echo "  make install-deps - Install required dependencies"