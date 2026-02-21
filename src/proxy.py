import json
import os
import time
import urllib.request
from threading import Lock
from typing import Any

import httpx
import jwt
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
JWT_REQUIRED_CLAIMS = ["exp", "sub"]
KID_MISS_REFETCH_COOLDOWN_SECONDS = 5 * 60
JWKS_FETCH_TIMEOUT_SECONDS = 5
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("HQG_PROXY_UPSTREAM_TIMEOUT_SECONDS", "30"))

_jwks_lock = Lock()
_jwks_cache: dict[str, dict[str, Any]] = {}
_last_kid_miss_refetch_at: dict[str, float] = {}


async def proxy_request(request: Request, base_url: str, upstream_path: str) -> Response:
    token = request.cookies.get("hqg_auth_token")
    if not token:
        return PlainTextResponse("Unauthorized", status_code=401)

    jwks_url = os.getenv("HQG_DASH_JWKS_URL", "")
    if not jwks_url:
        return PlainTextResponse("JWKS URL is not configured", status_code=500)

    if not _is_valid_jwt(token, jwks_url):
        return PlainTextResponse("Unauthorized", status_code=401)

    if not base_url:
        return PlainTextResponse("Upstream base URL is not configured", status_code=500)

    base = base_url.rstrip("/")
    path = f"/{upstream_path.lstrip('/')}" if upstream_path else "/"
    target_url = f"{base}{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    outbound_headers = dict(request.headers)
    outbound_headers.pop("host", None)
    body = await request.body()

    try:
        async with httpx.AsyncClient(follow_redirects=False) as client:
            downstream = await client.request(
                method=request.method,
                url=target_url,
                headers=outbound_headers,
                content=body,
                timeout=UPSTREAM_TIMEOUT_SECONDS,
            )
    except httpx.RequestError:
        return PlainTextResponse("Bad Gateway", status_code=502)

    return Response(
        content=downstream.content,
        status_code=downstream.status_code,
        headers=dict(downstream.headers),
    )


def _is_valid_jwt(token: str, jwks_url: str) -> bool:
    try:
        kid = jwt.get_unverified_header(token).get("kid")
        if not kid:
            return False

        jwks = _get_jwks(jwks_url, force_refresh=False)
        keys = ((jwks or {}).get("keys") or [])
        jwk = next((key for key in keys if key.get("kid") == kid), None)
        if not jwk:
            refreshed_jwks = _get_jwks(jwks_url, force_refresh=True)
            refreshed_keys = ((refreshed_jwks or {}).get("keys") or [])
            jwk = next((key for key in refreshed_keys if key.get("kid") == kid), None)
        if not jwk:
            return False

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": JWT_REQUIRED_CLAIMS},
        )
        return bool(payload.get("sub"))
    except Exception:
        return False


def _get_jwks(jwks_url: str, force_refresh: bool = True) -> dict[str, Any] | None:
    now = time.monotonic()

    with _jwks_lock:
        cached = _jwks_cache.get(jwks_url)
        if not force_refresh and cached is not None:
            return cached

        if force_refresh:
            last_refresh = _last_kid_miss_refetch_at.get(jwks_url, 0.0)
            if now - last_refresh < KID_MISS_REFETCH_COOLDOWN_SECONDS:
                return cached
            _last_kid_miss_refetch_at[jwks_url] = now

    try:
        with urllib.request.urlopen(jwks_url, timeout=JWKS_FETCH_TIMEOUT_SECONDS) as response:
            fresh = json.loads(response.read().decode("utf-8"))
    except Exception:
        with _jwks_lock:
            return _jwks_cache.get(jwks_url)

    with _jwks_lock:
        _jwks_cache[jwks_url] = fresh
    return fresh
