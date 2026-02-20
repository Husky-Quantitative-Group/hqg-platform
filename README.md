# hqg-platform

`hqg-platform` is a small FastAPI service that sits behind a reverse proxy and route traffic to internal services.

Current scope (initial scaffold):
- FastAPI app entrypoint in `src/server.py`
- Health check endpoint at `GET /health` returning `ok`
- Docker container for running the service on `0.0.0.0:$PORT`

## Local run

```bash
pip install fastapi uvicorn[standard]
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
