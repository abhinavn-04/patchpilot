# PatchPilot architecture and demo walkthrough

PatchPilot is a Python/FastAPI backend for safe, reviewable GitHub pull-request
analysis. The diagram shows the implemented components and their intended review
boundary. The background worker that connects the persisted webhook to the full
review-and-publish sequence is deliberately a future enhancement.

```mermaid
flowchart LR
    GH[GitHub pull request] --> WH[Verified webhook endpoint]
    WH --> WD[(Webhook deliveries)]

    GH --> API[GitHub REST client]
    API --> PR[Typed PR context and changed files]
    PR --> FILTER[Python-file filter]
    FILTER --> STATIC[Deterministic static analysis]
    STATIC --> FINDINGS[Normalized findings]

    PR -. bounded and redacted content .-> LLM[Provider-agnostic LLM reviewer]
    FINDINGS -. review context .-> LLM
    LLM --> VALIDATE[Structured finding validation]
    VALIDATE --> RANK[Deduplicate and confidence-rank]
    RANK --> PUBLISH[GitHub inline review comments]

    REVIEW[(Pull-request review jobs)] --> SUMMARY[GET /reviews/{review_id}]
    WD -. future worker creates and updates .-> REVIEW
    RANK -. future worker persists and publishes .-> REVIEW
```

## Local demo

### 1. Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn --env-file .env app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to inspect the health, readiness, webhook,
and review-summary API contracts.

### 2. Confirm service health

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Both endpoints return a JSON status response.

### 3. Exercise secure webhook intake

Follow the [local webhook test](../README.md#local-webhook-test) with a throwaway
secret. The first signed delivery is accepted; repeating the same delivery ID
returns `duplicate`, demonstrating signature verification and idempotency.

### 4. Run the deterministic portfolio demonstration

```bash
pytest -q
```

The test suite uses mocked GitHub transport: it verifies PR-file pagination,
inline-comment request payloads, error handling, confidence thresholds, secret
redaction, and review-summary responses without using a real GitHub token or
posting comments to a real pull request.

### 5. Run with Docker

```bash
docker compose up --build
```

The Compose service runs as a non-root user and stores its local SQLite database
in a named volume. Docker Compose is required for this command.

## Safety boundaries

- GitHub webhook signatures are verified over the untouched request body before
  a delivery is persisted.
- LLM-facing review content is bounded to the pull request and redacted for
  likely credentials before a provider adapter receives it.
- Only validated, high-confidence findings qualify for GitHub inline comments.
- Tests use fake providers and mock transports; they never require real secrets.
