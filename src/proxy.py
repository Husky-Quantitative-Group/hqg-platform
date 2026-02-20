import json
import os
import urllib.request
from functools import lru_cache

import httpx
import jwt
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
JWT_REQUIRED_CLAIMS = ["exp", "sub"]


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

        jwk = None
        for refresh in (False, True):
            keys = (_get_jwks(jwks_url).get("keys") or [])
            jwk = next((key for key in keys if key.get("kid") == kid), None)
            if jwk:
                break
            if not refresh:
                _get_jwks.cache_clear()

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


@lru_cache(maxsize=4)
def _get_jwks(jwks_url: str):
    with urllib.request.urlopen(jwks_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
