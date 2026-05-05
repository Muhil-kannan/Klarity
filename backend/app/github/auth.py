"""
GitHub App authentication.
Generates JWT tokens and installation access tokens.
"""

import time

import httpx
import jwt

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def generate_app_jwt() -> str:
    """
    Generate a short-lived JWT signed with the GitHub App's private key.
    Valid for 10 minutes (GitHub max is 10 minutes).
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,        # issued 60s ago to account for clock drift
        "exp": now + (9 * 60),  # expires in 9 minutes
        "iss": settings.GITHUB_APP_ID,
    }
    return jwt.encode(payload, settings.GITHUB_APP_PRIVATE_KEY, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    """
    Exchange a JWT for an installation access token.
    Installation tokens are valid for 1 hour.
    """
    app_jwt = generate_app_jwt()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        data = response.json()

    logger.debug("github.installation_token_obtained", installation_id=installation_id)
    return data["token"]
