import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import subprocess
import secrets

from src.proxy import PROXY_METHODS, proxy_request

DEPLOY_SECRET = os.getenv("DEPLOY_SECRET", "")

DEPLOY_SERVICES = {
    "hqg-status": "/home/software/hqg-status",
    "hqg-engine": "/home/software/hqg-engine",
    "hqg-platform": "/home/software/hqg-platform",
    "hqg-backtester": "/home/software/hqg-backtester",
}

app = FastAPI(title="hqg-platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dashboard.uconnquant.com",
        "http://localhost:5173"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    return "ok"


@app.api_route("/backtester", methods=PROXY_METHODS, include_in_schema=False)
@app.api_route("/backtester/{upstream_path:path}", methods=PROXY_METHODS, include_in_schema=False)
async def proxy_backtester(request: Request, upstream_path: str = "") -> Response:
    return await proxy_request(request, os.getenv("BACKTESTER_BASE_URL", ""), upstream_path)


@app.api_route("/engine", methods=PROXY_METHODS, include_in_schema=False)
@app.api_route("/engine/{upstream_path:path}", methods=PROXY_METHODS, include_in_schema=False)
async def proxy_engine(request: Request, upstream_path: str = "") -> Response:
    return await proxy_request(request, os.getenv("ENGINE_BASE_URL", ""), upstream_path)



@app.post("/deploy/{service}")
async def deploy(service: str, request: Request) -> Response:
    auth = request.headers.get("authorization", "")
    if not DEPLOY_SECRET or not secrets.compare_digest(auth, f"Bearer {DEPLOY_SECRET}"):
        return PlainTextResponse("Unauthorized", status_code=401)

    if service not in DEPLOY_SERVICES:
        return PlainTextResponse("Unknown service", status_code=404)

    path = DEPLOY_SERVICES[service]
    subprocess.Popen(
        ["bash", "-c", f"cd {path} && git pull && docker compose up -d"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return PlainTextResponse("deploying")