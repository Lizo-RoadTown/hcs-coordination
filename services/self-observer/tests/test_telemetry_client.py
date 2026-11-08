"""Tests for telemetry_client.py — the C1 swap of the v1 None-stub for a real
authenticated read of GET /telemetry/invocations.

Pins the three-way contract (mirrors read_api.py's 0-vs-None existence
contract) and the fail-soft rule (the client runs inside the production
cron and must never raise):
- active artifact         -> int
- known but 0 in window   -> 0 (NOT None — orphan territory)
- never seen (known=false)-> None
- 401 / 5xx / transport / non-JSON / non-numeric -> None
- Bearer OBSERVER_JWT attached iff configured
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

_SVC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SVC))

from config import AuthConfig, Endpoints  # noqa: E402
from telemetry_client import TelemetryClient  # noqa: E402


_ENDPOINTS = Endpoints(
    candidate_registry_url="http://test-arch",
    telemetry_query_url="http://test-tel",
    memory_url="http://test-mem",
)
_AUTH_NO_JWT = AuthConfig()
_AUTH_WITH_JWT = AuthConfig(observer_jwt="tok-abc")


def _mock_response(status: int, json_body=None, text_body=None) -> httpx.Response:
    req = httpx.Request("GET", "http://test-tel/telemetry/invocations")
    if text_body is not None:
        return httpx.Response(status, text=text_body, request=req)
    return httpx.Response(status, json=json_body or {}, request=req)


def _client(auth=_AUTH_WITH_JWT) -> TelemetryClient:
    return TelemetryClient(_ENDPOINTS, auth)


@pytest.mark.asyncio
async def test_active_artifact_returns_int():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(200, {
            "artifact_ref": "r#f", "window_days": 30,
            "invocations": 42, "known": True,
        })
    )):
        assert await _client().invocations_30d("r", "f") == 42


@pytest.mark.asyncio
async def test_known_but_zero_returns_zero_not_none():
    # The load-bearing distinction: 0 means instrumented-but-unused and may
    # drive an orphan candidate; it must NOT collapse into None.
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(200, {
            "invocations": 0, "known": True,
        })
    )):
        result = await _client().invocations_30d("r", "f")
        assert result == 0
        assert result is not None


@pytest.mark.asyncio
async def test_never_seen_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(200, {
            "invocations": None, "known": False,
        })
    )):
        assert await _client().invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_auth_rejected_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(401, {"detail": "no"})
    )):
        assert await _client(_AUTH_NO_JWT).invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_server_error_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(503, {"detail": "down"})
    )):
        assert await _client().invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_transport_error_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        side_effect=httpx.ConnectError("boom")
    )):
        assert await _client().invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_non_json_body_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(200, text_body="Internal Server Error")
    )):
        assert await _client().invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_non_numeric_invocations_returns_none():
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(
        return_value=_mock_response(200, {"invocations": "many", "known": True})
    )):
        assert await _client().invocations_30d("r", "f") is None


@pytest.mark.asyncio
async def test_jwt_header_attached_when_configured():
    mock_get = AsyncMock(return_value=_mock_response(
        200, {"invocations": 1, "known": True}))
    with patch.object(httpx.AsyncClient, "get", new=mock_get):
        await _client(_AUTH_WITH_JWT).invocations_30d("r", "f")
    _, kwargs = mock_get.call_args
    assert kwargs["headers"].get("Authorization") == "Bearer tok-abc"


@pytest.mark.asyncio
async def test_no_jwt_means_no_auth_header():
    mock_get = AsyncMock(return_value=_mock_response(
        200, {"invocations": 1, "known": True}))
    with patch.object(httpx.AsyncClient, "get", new=mock_get):
        await _client(_AUTH_NO_JWT).invocations_30d("r", "f")
    _, kwargs = mock_get.call_args
    assert "Authorization" not in kwargs["headers"]


@pytest.mark.asyncio
async def test_query_params_carry_repo_path_window():
    mock_get = AsyncMock(return_value=_mock_response(
        200, {"invocations": 1, "known": True}))
    with patch.object(httpx.AsyncClient, "get", new=mock_get):
        await _client().invocations_30d("Lizo-RoadTown/x", ".claude/skills/s/SKILL.md")
    _, kwargs = mock_get.call_args
    assert kwargs["params"] == {
        "repo": "Lizo-RoadTown/x",
        "file_path": ".claude/skills/s/SKILL.md",
        "window_days": 30,
    }
