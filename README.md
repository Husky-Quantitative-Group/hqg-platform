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
- `HQG_PROXY_UPSTREAM_TIMEOUT_SECONDS` (default: `30`; increase if upstream responses are slow)
- `PORT` (default `8080`)

## Releases

Merging a PR into `main` releases the service automatically:
1. `require-bump-label` requires the PR to carry exactly one label.
2. `release.yml` runs `make test`, builds the image, and tags it `X.Y.Z-<12-hex>`. Each release also gets a git tag `vX.Y.Z`.
3. It sends `service-released` to `hqg-deployment`, which deploys the image.

Version bump from the label:
- `breaking`: major (X)
- `feature`: minor (Y)
- any other single label: patch (Z)

## Tests

`make test` runs `pytest tests`. Add test files under `tests/`.

## Run with Docker Compose

```bash
docker compose up --build
```

Run detached:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

## Debugging `502 Bad Gateway`

`hqg-platform` returns `502` only when forwarding to upstream throws an `httpx.RequestError` (for example DNS, connection, or timeout).

1. Tail proxy logs while reproducing:

```bash
docker compose logs -f hqg-platform
```

2. Look for:
   - `Upstream request failed ... error_type=ConnectError` -> host/port/network issue
   - `... error_type=ReadTimeout` -> upstream too slow for current timeout

3. If needed, increase `HQG_PROXY_UPSTREAM_TIMEOUT_SECONDS` and restart:

```bash
docker compose up -d --build
```
