"""Mode tests for loom_auth.auth_bridge.verify_bearer.

Pins the two-mode commitment (module docstring, "Two-mode commitment"):
self-host requires BOTH no Authorization header AND no LOOM_JWT_PUBLIC_KEY.
A configured public key means hosted deployment, where anonymous requests
are rejected (mode 4, added 2026-11-07 after the live registry served
self-host tenant data to unauthenticated callers).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom_auth import auth_bridge  # noqa: E402

# A syntactically valid RSA public key that signs nothing we send — any
# bearer token checked against it fails signature verification.
_UNRELATED_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredZiKRkgwlL9xNAwxXFg0x/XFw005UWVRIkdg
cKWTjpBP2dPwVZ4WWC+9aGVd+Gyn1o0CLelf4rEjGoXbAAEgAqeGUxrcIlbjXfbc
mwIDAQAB
-----END PUBLIC KEY-----"""


def _call(authorization):
    return asyncio.run(auth_bridge.verify_bearer(authorization=authorization))


def _set_key(monkeypatch, value):
    """Reset the process-wide key cache, then set/unset the env var."""
    auth_bridge._public_key_cache = None
    if value is None:
        monkeypatch.delenv("LOOM_JWT_PUBLIC_KEY", raising=False)
    else:
        monkeypatch.setenv("LOOM_JWT_PUBLIC_KEY", value)


def test_self_host_no_header_no_key(monkeypatch):
    """Mode 1: anonymous + keyless = self-host tenant (unchanged behavior)."""
    _set_key(monkeypatch, None)
    assert _call(None) == auth_bridge.SELF_HOST_TENANT_ID


def test_anonymous_rejected_when_key_configured(monkeypatch):
    """Mode 4: anonymous on a hosted deployment (key set) must 401,
    never inherit the self-host tenant."""
    _set_key(monkeypatch, _UNRELATED_PUBLIC_KEY)
    with pytest.raises(HTTPException) as exc:
        _call(None)
    assert exc.value.status_code == 401


def test_bearer_without_key_rejected(monkeypatch):
    """Mode 3 variant: caller tried to authenticate but server has no key
    — 401, no silent self-host fallback."""
    _set_key(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        _call("Bearer some-token")
    assert exc.value.status_code == 401


def test_malformed_header_rejected(monkeypatch):
    _set_key(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        _call("NotBearer")
    assert exc.value.status_code == 401


def test_invalid_token_rejected_when_key_configured(monkeypatch):
    """Mode 3: bearer present, key set, signature does not verify — 401."""
    _set_key(monkeypatch, _UNRELATED_PUBLIC_KEY)
    with pytest.raises(HTTPException) as exc:
        _call("Bearer not.a.jwt")
    assert exc.value.status_code == 401


def teardown_module(module):
    """Leave no cached key behind for other test modules in the process."""
    auth_bridge._public_key_cache = None
