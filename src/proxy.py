import httpx
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


def _build_target_url(base_url: str, upstream_path: str, query: str) -> str:
    base = base_url.rstrip("/")
    path = f"/{upstream_path.lstrip('/')}" if upstream_path else "/"
    if query:
        return f"{base}{path}?{query}"
    return f"{base}{path}"


async def proxy_request(request: Request, base_url: str, upstream_path: str) -> Response:
    if not request.cookies.get("hqg_auth_token"):
        return PlainTextResponse("Unauthorized", status_code=401)

    if not base_url:
        return PlainTextResponse("Upstream base URL is not configured", status_code=500)

    target_url = _build_target_url(base_url, upstream_path, request.url.query)
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
