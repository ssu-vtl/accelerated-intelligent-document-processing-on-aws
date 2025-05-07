# Makefile for code quality and formatting

# Run both linting and formatting in one command
lint: ruff-lint format

# Run linting checks and fix issues automatically
ruff-lint:
	ruff check --fix

# Format code according to project standards
format:
	ruff format

# CI/CD version of lint that only checks but doesn't modify files
# Used in CI pipelines to verify code quality without making changes
lint-cicd:
	ruff check && \
	ruff format --check