.PHONY: help run fmt test clean install dev-install lint

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  dev-install  - Install package with dev dependencies"
	@echo "  run          - Run job analysis CLI (example command)"
	@echo "  fmt          - Format code with ruff"
	@echo "  lint         - Lint code with ruff"
	@echo "  test         - Run tests with pytest"
	@echo "  clean        - Clean build artifacts and cache files"

# Installation targets
install:
	uv pip install -e .

dev-install:
	uv pip install -e .[dev]

# Development targets
fmt:
	ruff format .

lint:
	ruff check .

test:
	pytest -v

# Example run command (user needs to set API keys in .env file)
run:
	python src/job_analysis/cli.py  run --input-csv data/Job\ applications\ -\ 2024_2025.csv

# Cleanup targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f jobs_analyzed.csv requirements_frequency.csv
	rm -rf notebooks/.ipynb_checkpoints
	rm -rf dist/ build/

# Combined targets
check: lint test
	@echo "All checks passed!"

ci: dev-install check
	@echo "CI pipeline completed successfully!"
