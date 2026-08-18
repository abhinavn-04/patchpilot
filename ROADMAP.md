# PatchPilot roadmap

Each item is a small, independently reviewable change.

## Week 1 — Foundation

- [x] Initialize repository structure, development tooling, and project documentation.
- [x] Add FastAPI health and readiness endpoints.
- [x] Add PostgreSQL models for pull-request review jobs.
- [x] Cover review-job persistence with tests.

## Week 2 — GitHub integration

- [x] Verify GitHub webhook signatures.
- [x] Persist idempotent webhook deliveries.
- [x] Fetch pull-request metadata and changed files.
- [x] Cover duplicate and invalid webhook deliveries.

## Week 3 — Deterministic review pipeline

- [x] Filter generated and unsupported files.
- [x] Add a Python static-analysis review stage.
- [x] Normalize findings with severity levels.
- [x] Document local webhook testing.

## Week 4 — LLM review

- [x] Add a provider-agnostic LLM reviewer interface.
- [x] Validate structured LLM findings.
- [x] Add a fake LLM reviewer for deterministic tests.
- [x] Redact likely secrets before external review.

## Week 5 — Feedback publishing

- [x] Deduplicate and confidence-rank findings.
- [x] Publish high-confidence findings to GitHub pull requests.
- [x] Add a review-summary endpoint.
- [x] Test GitHub review-comment publishing.

## Week 6 — Portfolio finish

- [x] Add a Docker development environment.
- [x] Add test and lint CI.
- [x] Add an architecture diagram and demo walkthrough.
- [x] Prepare the repository for portfolio use.
