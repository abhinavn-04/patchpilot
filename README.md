# PatchPilot

PatchPilot is a Python service that reviews GitHub pull requests using deterministic
static checks and bounded LLM analysis. It will validate webhook deliveries, process
only relevant changed files, and publish high-confidence findings as actionable PR
feedback.

## Planned capabilities

- GitHub webhook verification and idempotent delivery processing
- Pull-request diff collection and source-file filtering
- Static analysis alongside structured LLM findings
- Confidence thresholds, deduplication, and GitHub review comments
- PostgreSQL persistence, background workers, tests, Docker, and CI

## Technology direction

Python, FastAPI, PostgreSQL, Redis, GitHub webhooks/API, and a provider-agnostic
LLM adapter. No provider credential is required until the LLM milestone.

## Development setup

This repository is intentionally at its initialization stage. The first runnable API
endpoint will be added in the next milestone.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for commit-sized milestones.
