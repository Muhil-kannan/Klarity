"""
GitHub webhook receiver.
Accepts events from GitHub, validates signatures, and enqueues background jobs.
"""

import json
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Header, Request, Response, status
from sqlmodel import select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import verify_webhook_signature
from app.db.models import WebhookEvent
from app.db.session import get_session

logger = get_logger(__name__)

router = APIRouter()

HANDLED_EVENTS = {
    "pull_request": ["opened", "edited", "synchronize", "reopened"],
    "issues": ["opened", "edited"],
    "ping": ["*"],
}


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
) -> Response:
    """
    Receive GitHub webhook events.
    Always returns 200 immediately — processing happens in the background.
    """
    body = await verify_webhook_signature(request)
    payload: dict[str, Any] = json.loads(body)

    logger.info(
        "webhook.received",
        gh_event=x_github_event,
        delivery_id=x_github_delivery,
        repo=payload.get("repository", {}).get("full_name", "unknown"),
    )

    if x_github_event == "ping":
        return Response(content='{"message": "pong"}', media_type="application/json")

    action = payload.get("action", "")
    handled_actions = HANDLED_EVENTS.get(x_github_event, [])
    if not handled_actions or (action not in handled_actions and "*" not in handled_actions):
        logger.debug("webhook.ignored", gh_event=x_github_event, action=action)
        return Response(content='{"message": "ignored"}', media_type="application/json")

    # Replay protection — reject duplicate delivery IDs
    async for session in get_session():
        existing = await session.exec(
            select(WebhookEvent).where(WebhookEvent.delivery_id == x_github_delivery)
        )
        if existing.first():
            logger.warning("webhook.duplicate", delivery_id=x_github_delivery)
            return Response(content='{"message": "duplicate"}', media_type="application/json")

        event_record = WebhookEvent(
            delivery_id=x_github_delivery,
            event_type=x_github_event,
            action=action,
            repo_full_name=payload.get("repository", {}).get("full_name", "unknown"),
            payload_summary=json.dumps({
                "pr_number": payload.get("pull_request", {}).get("number"),
                "issue_number": payload.get("issue", {}).get("number"),
                "author": (
                    payload.get("pull_request", {}).get("user", {}).get("login")
                    or payload.get("issue", {}).get("user", {}).get("login")
                ),
            }),
        )
        session.add(event_record)

    # Enqueue background job
    if x_github_event == "pull_request":
        await _enqueue_job("process_pull_request_event", payload, x_github_delivery)
    elif x_github_event == "issues":
        await _enqueue_job("process_issue_event", payload, x_github_delivery)

    return Response(content='{"message": "queued"}', media_type="application/json")


async def _enqueue_job(function_name: str, payload: dict[str, Any], delivery_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    await redis.enqueue_job(function_name, payload=payload, delivery_id=delivery_id)
    await redis.aclose()  # type: ignore[attr-defined]
    logger.info("webhook.job_enqueued", function=function_name, delivery_id=delivery_id)
