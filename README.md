# hqg-platform

`hqg-platform` is a small FastAPI service behind a reverse proxy that routes traffic to internal services.

Current scope:
- `GET /health` returns `ok` (no auth).
- `/backtester/*` proxies to `BACKTESTER_BASE_URL` (prefix stripped).
- `/engine/*` proxies to `ENGINE_BASE_URL` (prefix stripped).

## Configuration

Set these env vars (see `example.env`):
- `BACKTESTER_BASE_URL` (example: `http://10.0.0.12:8000`)
- `ENGINE_BASE_URL` (example: `http://10.0.0.13:8000`)
- `HQG_DASH_JWKS_URL` (example: `https://platform.uconnquant.com/.well-known/jwks.json`)
- `PORT` (default `8080`)

## Local run

```bash
pip install fastapi httpx 'pyjwt[crypto]' uvicorn[standard]
uvicorn src.server:app --host 0.0.0.0 --port 8080
```

Check health:

```bash
curl http://localhost:8080/health
```

## Docker run

```bash
docker build -t hqg-platform .
docker run --rm -p 8080:8080 -e PORT=8080 hqg-platform
```
