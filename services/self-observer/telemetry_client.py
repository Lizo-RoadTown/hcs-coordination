"""Read invocation counts from telemetry-ingestion's authenticated read API.

C1 (wire X4, docs/plans/2026-10-21-master-plan-personal-loop.md): the v1 stub
returned None for every query, so no signal rule could ever see real usage.
The read API went live with the 2026-11-08 telemetry cutover
(GET /telemetry/invocations — services/telemetry-ingestion/read_api.py:128),
and this client now performs the real query.

Contract — mirrors the API's 0-vs-None existence contract exactly:
    never seen anywhere    -> None (signal_rules suppresses orphan candidates)
    seen, 0 in the window  -> 0    (instrumented-but-unused: orphan territory)
    active                 -> int

Fail-soft is load-bearing: this runs inside the 6-hourly production cron
(crn-daedvggu01pc73e3r820). Any transport error, timeout, auth rejection or
malformed body degrades to None ("telemetry unavailable") — it never raises.
Auth: Bearer OBSERVER_JWT when configured (same pattern as
candidate_client.py:84); without it the read API answers 401 and this client
returns None, so unauthenticated local runs degrade instead of crashing.
"""
from __future__ import annotations

import logging

import httpx

from config import AuthConfig, Endpoints

logger = logging.getLogger(__name__)

_WINDOW_DAYS = 30
_TIMEOUT_S = 30.0


class TelemetryClient:
    """Reads invocation counts from the live telemetry read API."""

    def __init__(self, endpoints: Endpoints, auth: AuthConfig | None = None):
        self.endpoints = endpoints
        self.auth = auth or AuthConfig()

    async def invocations_30d(self, repo: str, file_path: str) -> int | None:
        """Return the invocation count over the last 30 days for an entry.

        Returns:
            None if telemetry is unavailable OR the artifact has never been
            seen (the API's known=false case) — callers suppress.
            int (including 0) when the artifact is known; 0 means
            instrumented-but-unused and may drive an orphan candidate.
        """
        url = (
            f"{self.endpoints.telemetry_query_url.rstrip('/')}"
            "/telemetry/invocations"
        )
        headers: dict[str, str] = {}
        if self.auth.observer_jwt:
            headers["Authorization"] = f"Bearer {self.auth.observer_jwt}"
        params = {
            "repo": repo,
            "file_path": file_path,
            "window_days": _WINDOW_DAYS,
        }
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT_S, follow_redirects=True
            ) as client:
                resp = await client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning(
                "telemetry read failed (transport) for %s/%s: %s",
                repo, file_path, exc,
            )
            return None

        if resp.status_code != 200:
            logger.warning(
                "telemetry read failed for %s/%s: HTTP %s",
                repo, file_path, resp.status_code,
            )
            return None

        try:
            body = resp.json()
        except ValueError:
            logger.warning(
                "telemetry read returned non-JSON for %s/%s", repo, file_path
            )
            return None

        invocations = body.get("invocations")
        if invocations is None:
            # known=false — never instrumented anywhere. Suppress downstream.
            return None
        try:
            return int(invocations)
        except (TypeError, ValueError):
            logger.warning(
                "telemetry read returned non-numeric invocations for %s/%s",
                repo, file_path,
            )
            return None
