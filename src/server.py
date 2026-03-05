import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from src.proxy import PROXY_METHODS, proxy_request

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
