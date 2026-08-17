import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import Base, WebhookDelivery
from app.webhooks import verify_github_signature

client = TestClient(app)


def github_signature(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def webhook_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def github_headers(
    payload: bytes, secret: str, delivery_id: str = "delivery-123"
) -> dict[str, str]:
    return {
        "X-Hub-Signature-256": github_signature(payload, secret),
        "X-GitHub-Delivery": delivery_id,
        "X-GitHub-Event": "pull_request",
    }


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


def test_webhook_endpoint_accepts_valid_delivery(monkeypatch, webhook_database) -> None:
    secret = "test-secret"
    payload = b'{"action":"opened"}'
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=github_headers(payload, secret),
    )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "delivery_id": "delivery-123"}

    with webhook_database() as session:
        delivery = session.query(WebhookDelivery).one()
        assert delivery.github_delivery_id == "delivery-123"
        assert delivery.event_name == "pull_request"
        assert delivery.payload == payload


def test_webhook_endpoint_ignores_duplicate_delivery(monkeypatch, webhook_database) -> None:
    secret = "test-secret"
    payload = b'{"action":"opened"}'
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
    headers = github_headers(payload, secret)

    assert client.post("/webhooks/github", content=payload, headers=headers).status_code == 202
    response = client.post("/webhooks/github", content=payload, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"status": "duplicate", "delivery_id": "delivery-123"}

    with webhook_database() as session:
        assert session.query(WebhookDelivery).count() == 1


def test_webhook_endpoint_rejects_invalid_signature(monkeypatch, webhook_database) -> None:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")

    response = client.post(
        "/webhooks/github",
        content=b'{"action":"opened"}',
        headers={"X-Hub-Signature-256": "sha256=invalid", "X-GitHub-Delivery": "delivery-123"},
    )

    assert response.status_code == 403
    with webhook_database() as session:
        assert session.query(WebhookDelivery).count() == 0


def test_webhook_endpoint_requires_delivery_metadata(monkeypatch, webhook_database) -> None:
    secret = "test-secret"
    payload = b'{"action":"opened"}'
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers={
            "X-Hub-Signature-256": github_signature(payload, secret),
            "X-GitHub-Delivery": "delivery-123",
        },
    )

    assert response.status_code == 400
    with webhook_database() as session:
        assert session.query(WebhookDelivery).count() == 0


def test_webhook_endpoint_requires_configured_secret(monkeypatch, webhook_database) -> None:
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)

    response = client.post("/webhooks/github", content=b"{}")

    assert response.status_code == 503
