# PatchPilot

PatchPilot is a Python/FastAPI backend for safe, reviewable GitHub pull-request
analysis. It verifies webhook deliveries, gathers typed pull-request context, applies
deterministic checks, validates bounded LLM findings, and prepares high-confidence
inline feedback for GitHub.

## Portfolio highlights

- Verified GitHub webhook intake using HMAC-SHA256 over untouched request bytes,
  with idempotent delivery persistence.
- Typed GitHub pull-request retrieval, pagination, conservative Python-file filtering,
  and line-aware static checks for security and reliability risks.
- Provider-independent LLM boundary with structured-output validation, deterministic
  fake adapters, likely-secret redaction, confidence ranking, and deduplication.
- High-confidence GitHub inline-comment publishing contract, tested entirely with
  mock transport so local tests never post to a real pull request.
- FastAPI health, readiness, and durable review-summary endpoints backed by SQLAlchemy.
- Docker development environment, GitHub Actions lint/test CI, and 45 automated tests.

## Current scope

The repository implements and tests the components above. The production background
worker that connects an accepted webhook to the end-to-end review-and-publish sequence
is intentionally not implemented yet; the architecture diagram marks that boundary as
future work. No real LLM provider or GitHub credential is required to run the tests.

## Technology direction

Python, FastAPI, PostgreSQL, Redis, GitHub webhooks/API, and a provider-agnostic
LLM adapter. No provider credential is required until the LLM milestone.

## Development setup

Run the API locally:

```bash
cp .env.example .env
# Set GITHUB_WEBHOOK_SECRET to a long random value before using webhooks.
uvicorn --env-file .env app.main:app --reload
```

Then visit:

- `http://127.0.0.1:8000/health` for liveness
- `http://127.0.0.1:8000/ready` for readiness
- `http://127.0.0.1:8000/docs` for interactive API documentation

### Docker development

Run the service with a persistent local SQLite database:

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000/docs`. The container runs as a non-root user;
the named `patchpilot_data` volume keeps the local database between restarts.
Set `GITHUB_WEBHOOK_SECRET` only when testing webhook delivery, for example:

```bash
GITHUB_WEBHOOK_SECRET='local-only-secret' docker compose up --build
```

## GitHub webhooks

`POST /webhooks/github` validates the raw request body with GitHub's
`X-Hub-Signature-256` HMAC-SHA256 header before accepting a delivery. The next
step persists each verified delivery idempotently before processing it. Local
development uses SQLite; set `DATABASE_URL` to a PostgreSQL connection URL when
running against PostgreSQL.

The GitHub API client uses `GITHUB_TOKEN` to fetch pull-request metadata and
every changed file, including paginated results. Use a GitHub App or a
fine-grained token with read access to pull requests; the token is not needed
for the local test suite.

### Local webhook test

Use a throwaway secret and SQLite for a local smoke test. Do not use a real
GitHub webhook secret in a terminal history, source file, or commit.

```bash
export GITHUB_WEBHOOK_SECRET='local-only-secret'
uvicorn app.main:app --reload
```

In a second terminal, create the exact JSON payload and calculate the HMAC over
those unchanged bytes. The `X-GitHub-Delivery` value must be unique for a new
delivery.

```bash
export PAYLOAD='{"action":"opened"}'
export SIGNATURE="$(python3 -c 'import hashlib,hmac,os; print("sha256=" + hmac.new(os.environ["GITHUB_WEBHOOK_SECRET"].encode(), os.environ["PAYLOAD"].encode(), hashlib.sha256).hexdigest())")"

curl --request POST http://127.0.0.1:8000/webhooks/github \
  --header "X-Hub-Signature-256: ${SIGNATURE}" \
  --header 'X-GitHub-Delivery: local-delivery-001' \
  --header 'X-GitHub-Event: pull_request' \
  --header 'Content-Type: application/json' \
  --data "${PAYLOAD}"
```

The first request returns `202` with `{"status":"accepted"}`. Repeat the
same request with the same delivery id to confirm idempotency; it returns `200`
with `{"status":"duplicate"}`. Change either the payload or signature to
confirm that invalid signatures are rejected with `403`.

## Review scope

The first deterministic review stage accepts Python (`.py`) diffs only. It
skips deleted files, files without a GitHub patch, lockfiles, build output,
vendored dependencies, generated protobuf code, source maps, and binary files.
Additional language support can be added without weakening these guardrails.

It inspects only newly added Python lines and emits raw signals for `eval`/`exec`,
`subprocess` calls using `shell=True`, literal credential assignments, and bare
`except` blocks. Signals are normalized into review findings: command-execution and
credential risks are `high`, bare exceptions are `medium`, and unknown future rules
default to `low` until explicitly classified.

LLM review uses a provider-independent interface. The core service passes bounded
pull-request context, reviewable files, and normalized static findings to an adapter;
the default adapter raises a configuration error and never makes a network call.
Provider responses must be JSON with a `findings` array. Each finding is validated
against changed-file paths, a positive line number, `low`/`medium`/`high` severity,
and a confidence score from 0 to 1 before it can enter the pipeline.

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

GitHub Actions runs Ruff and the full pytest suite for every pull request and
push to `main`.

## Resume-ready description

**PatchPilot — Python, FastAPI, SQLAlchemy, pytest, Docker, GitHub REST API**

Built a secure pull-request review backend with verified and idempotent GitHub
webhooks, typed PR-diff retrieval, deterministic Python checks, validated structured
LLM findings, secret redaction, confidence ranking, and line-level comment publishing
contracts. Added Docker-based local development and GitHub Actions CI with Ruff and
pytest.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for commit-sized milestones.

For the component diagram and a safe local demonstration, see
[Architecture and demo walkthrough](docs/architecture.md).
