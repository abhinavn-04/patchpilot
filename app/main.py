"""HTTP entry point for PatchPilot."""

from fastapi import FastAPI

app = FastAPI(
    title="PatchPilot",
    version="0.1.0",
    description="AI-assisted GitHub pull-request review service.",
)


@app.get("/health", tags=["operations"])
async def health_check() -> dict[str, str]:
    """Report that the HTTP process is running."""
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
async def readiness_check() -> dict[str, str]:
    """Report readiness to accept review work.

    Dependency checks will be added alongside PostgreSQL and Redis integration.
    """
    return {"status": "ready"}
