"""
GitHub webhook signature verification.
Ensures incoming webhooks are genuinely from GitHub.
"""

import hashlib
import hmac

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_webhook_signature(request: Request) -> bytes:
    """
    Verify the X-Hub-Signature-256 header sent by GitHub.
    Raises HTTP 401 if the signature is missing or invalid.
    Returns the raw request body for further processing.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        logger.warning("webhook.signature_missing", ip=request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )

    body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        logger.warning("webhook.signature_invalid", ip=request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    return body
