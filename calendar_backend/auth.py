"""HTTP identity for calendar reads and MCP gateway requests."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from workforce_agent.agent import Principal
from workforce_agent.config import get_settings


demo_identities: dict[str, tuple[Principal, datetime]] = {}


def browser_identity(request: Request) -> Principal:
    settings = get_settings()
    authorization = request.headers.get('authorization', '')
    if authorization:
        if not authorization.startswith('Bearer '):
            raise HTTPException(401, 'Invalid credentials')
        token = authorization.removeprefix('Bearer ')
        for configured, claims in settings.agent_credentials.items():
            if secrets.compare_digest(token, configured):
                return Principal.model_validate(claims)
        raise HTTPException(401, 'Invalid credentials')

    cookie = request.cookies.get('calendar_demo_identity', '')
    record = demo_identities.get(cookie)
    if settings.agent_demo_enabled and record and record[1] > datetime.now(timezone.utc):
        return record[0]
    raise HTTPException(401, 'Authentication required')
