.PHONY: help install lint type test demo-gif serve validate

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## Install package with dev deps
	pip install -e ".[dev]"

lint: ## Run ruff linter
	ruff check src tests
	ruff format --check src tests

type: ## Run mypy
	mypy src/interview_agent

test: ## Run pytest
	pytest tests/ -v --cov=interview_agent --cov-report=term-missing

demo-gif: ## Generate demo GIF asset
	python scripts/generate_demo_gif.py

serve: ## Start demo web server
	interview-agent serve --host 127.0.0.1 --port 8080

validate: lint type test ## Run all checks
