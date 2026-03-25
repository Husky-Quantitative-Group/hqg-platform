import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import subprocess
import secrets
from pathlib import Path

from src.proxy import PROXY_METHODS, proxy_request

LOGS_DIR = Path("/home/software/hqg-platform/logs")
LOGS_DIR.mkdir(exist_ok=True)

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


DEPLOY_SECRET = os.getenv("DEPLOY_SECRET", "")

DEPLOY_SCRIPTS = {
    "hqg-status": "/home/software/scripts-deployment/hqg-status.sh",
    "hqg-engine": "/home/software/scripts-deployment/hqg-engine.sh",
    "hqg-platform": "/home/software/scripts-deployment/hqg-platform.sh",
    "hqg-backtester": "/home/software/scripts-deployment/hqg-backtester.sh",
}

@app.post("/deploy/{service}")
async def deploy(service: str, request: Request) -> Response:
    auth = request.headers.get("authorization", "")
    if not DEPLOY_SECRET or not secrets.compare_digest(auth, f"Bearer {DEPLOY_SECRET}"):
        return PlainTextResponse("Unauthorized", status_code=401)

    if service not in DEPLOY_SCRIPTS:
        return PlainTextResponse(f"Unknown service: {service}", status_code=404)

    script = DEPLOY_SCRIPTS[service]

    if not os.path.isfile(script):
        return PlainTextResponse(f"deploy script not found for service: {service}", status_code=500)

    log_file = LOGS_DIR / f"deploy-{service}.log"
    f = open(log_file, "w")
    subprocess.Popen(
        ["bash", script],
        stdout=f,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )

    return PlainTextResponse(f"deploying {service}")