"""Validation helpers for inbound GitHub webhooks."""

import hashlib
import hmac


def verify_github_signature(
    *, payload: bytes, signature: str | None, secret: str
) -> bool:
    """Return whether a GitHub HMAC-SHA256 webhook signature is valid."""
    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
