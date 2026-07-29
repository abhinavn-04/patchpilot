# PatchPilot roadmap

Each item is a small, independently reviewable change.

## Week 1 — Foundation

- [x] Initialize repository structure, development tooling, and project documentation.
- [x] Add FastAPI health and readiness endpoints.
- [x] Add PostgreSQL models for pull-request review jobs.
- [ ] Cover review-job persistence with tests.

## Week 2 — GitHub integration

- [ ] Verify GitHub webhook signatures.
- [ ] Persist idempotent webhook deliveries.
- [ ] Fetch pull-request metadata and changed files.
- [ ] Cover duplicate and invalid webhook deliveries.

## Week 3 — Deterministic review pipeline

- [ ] Filter generated and unsupported files.
- [ ] Add a Python static-analysis review stage.
- [ ] Normalize findings with severity levels.
- [ ] Document local webhook testing.

## Week 4 — LLM review

- [ ] Add a provider-agnostic LLM reviewer interface.
- [ ] Validate structured LLM findings.
- [ ] Add a fake LLM reviewer for deterministic tests.
- [ ] Redact likely secrets before external review.

## Week 5 — Feedback publishing

- [ ] Deduplicate and confidence-rank findings.
- [ ] Publish high-confidence findings to GitHub pull requests.
- [ ] Add a review-summary endpoint.
- [ ] Test GitHub review-comment publishing.

## Week 6 — Portfolio finish

- [ ] Add a Docker development environment.
- [ ] Add test and lint CI.
- [ ] Add an architecture diagram and demo walkthrough.
- [ ] Prepare the repository for portfolio use.
