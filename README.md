# PatchPilot

PatchPilot is a Python service that reviews GitHub pull requests using deterministic
static checks and bounded LLM analysis. It will validate webhook deliveries, process
only relevant changed files, and publish high-confidence findings as actionable PR
feedback.

## Planned capabilities

- GitHub webhook verification and idempotent delivery processing
- PostgreSQL-backed pull-request review jobs with lifecycle state and duplicate protection
- Pull-request diff collection and source-file filtering
- Static analysis alongside structured LLM findings
- Confidence thresholds, deduplication, and GitHub review comments
- PostgreSQL persistence, background workers, tests, Docker, and CI

## Technology direction

Python, FastAPI, PostgreSQL, Redis, GitHub webhooks/API, and a provider-agnostic
LLM adapter. No provider credential is required until the LLM milestone.

## Development setup

Run the API locally:

```bash
cp .env.example .env
# Set GITHUB_WEBHOOK_SECRET to a long random value before using webhooks.
uvicorn app.main:app --reload
```

Then visit:

- `http://127.0.0.1:8000/health` for liveness
- `http://127.0.0.1:8000/ready` for readiness
- `http://127.0.0.1:8000/docs` for interactive API documentation

## GitHub webhooks

`POST /webhooks/github` validates the raw request body with GitHub's
`X-Hub-Signature-256` HMAC-SHA256 header before accepting a delivery. The next
milestone will persist accepted deliveries idempotently before processing them.

Run the tests with:

```bash
pytest
```

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for commit-sized milestones.
