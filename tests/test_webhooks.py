import hashlib
import hmac

from fastapi.testclient import TestClient

from app.main import app
from app.webhooks import verify_github_signature

client = TestClient(app)


def github_signature(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_signature_matches_github_documented_example() -> None:
    assert verify_github_signature(
        payload=b"Hello, World!",
        secret="It's a Secret to Everybody",
        signature="sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17",
    )


def test_signature_rejects_tampered_payload_and_invalid_header() -> None:
    payload = b'{"action":"opened"}'
    secret = "test-secret"

    assert not verify_github_signature(
        payload=payload + b" ",
        secret=secret,
        signature=github_signature(payload, secret),
    )
    assert not verify_github_signature(payload=payload, secret=secret, signature="sha1=wrong")


def test_webhook_endpoint_accepts_valid_delivery(monkeypatch) -> None:
    secret = "test-secret"
    payload = b'{"action":"opened"}'
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers={"X-Hub-Signature-256": github_signature(payload, secret)},
    )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}


def test_webhook_endpoint_rejects_invalid_signature(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")

    response = client.post(
        "/webhooks/github",
        content=b'{"action":"opened"}',
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )

    assert response.status_code == 403


def test_webhook_endpoint_requires_configured_secret(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)

    response = client.post("/webhooks/github", content=b"{}")

    assert response.status_code == 503
