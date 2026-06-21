#!/usr/bin/env bash
# Build phased git history: feature branches -> develop -> main
set -euo pipefail
cd "$(dirname "$0")/.."

git init -b main
git add .gitignore LICENSE
git commit -m "chore: initialize repository with license and gitignore"

git checkout -b develop

commit_phase() {
  local branch="$1"
  local message="$2"
  shift 2
  git checkout develop
  git checkout -b "$branch"
  git add "$@"
  git commit -m "$message"
  git checkout develop
  git merge --no-ff "$branch" -m "merge: $branch into develop"
  git branch -d "$branch"
}

# Phase 1: scaffold
commit_phase feature/project-scaffold "feat: add pyproject, Makefile, and package scaffold" \
  pyproject.toml Makefile .env.example alembic.ini migrations/

# Phase 2: models
commit_phase feature/domain-models "feat: add core domain models and configuration" \
  src/interview_agent/__init__.py src/interview_agent/config.py src/interview_agent/models.py

# Phase 3: lifecycle
commit_phase feature/state-machine-event-log "feat: add state machine and durable event log" \
  src/interview_agent/lifecycle/

# Phase 4: decision engine
commit_phase feature/decision-engine "feat: add deterministic decision engine with rationale traces" \
  src/interview_agent/decision/

# Phase 5: LLM base + openai/anthropic
commit_phase feature/llm-adapters-core "feat: add LLM adapter base, OpenAI and Anthropic integrations" \
  src/interview_agent/llm/base.py src/interview_agent/llm/openai_adapter.py \
  src/interview_agent/llm/anthropic_adapter.py src/interview_agent/llm/mock_adapter.py

# Phase 6: gemini + kimi + router
commit_phase feature/llm-adapters-extended "feat: add Gemini, Kimi, and LLM router" \
  src/interview_agent/llm/gemini_adapter.py src/interview_agent/llm/kimi_adapter.py \
  src/interview_agent/llm/router.py src/interview_agent/llm/__init__.py

# Phase 7: tools
commit_phase feature/tools-knowledge-base "feat: add tool adapters and interview KB search" \
  src/interview_agent/tools/ knowledge/

# Phase 8: safety
commit_phase feature/safety-controls "feat: add safety guard with timeout, scope, and cancellation" \
  src/interview_agent/safety/

# Phase 9: agent runner
commit_phase feature/agent-runner "feat: add agent orchestrator with full run lifecycle" \
  src/interview_agent/agent/

# Phase 10: API + demo UI
commit_phase feature/api-demo-ui "feat: add FastAPI server and web demo UI" \
  src/interview_agent/api/ src/interview_agent/cli.py demo/

# Phase 11: tests
commit_phase feature/tests "test: add unit and integration test suite" \
  tests/

# Phase 12: CI
commit_phase feature/ci-workflow "ci: add GitHub Actions lint, typecheck, and test workflow" \
  .github/

# Phase 13: docs
commit_phase feature/docs "docs: add README, QUICKSTART, ARCHITECTURE, SAFETY, CONFIGURATION" \
  README.md QUICKSTART.md CONFIGURATION.md SAFETY.md ARCHITECTURE.md CHANGELOG.md

# Phase 14: demo assets + scripts
commit_phase feature/demo-assets "feat: add demo GIF generator and assets" \
  scripts/ assets/

# Merge develop -> main (not direct feature -> main)
git checkout main
git merge --no-ff develop -m "release: merge develop into main — interview agent v0.1.0"

echo "Git history built: $(git log --oneline | wc -l | tr -d ' ') commits on $(git branch -a | wc -l) branches"
