"""Persistence for idempotent GitHub webhook deliveries."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import WebhookDelivery


def record_webhook_delivery(
    session: Session, *, delivery_id: str, event_name: str, payload: bytes
) -> bool:
    """Store one delivery and return whether it was newly created."""
    session.add(
        WebhookDelivery(
            github_delivery_id=delivery_id,
            event_name=event_name,
            payload=payload,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return False
    return True
