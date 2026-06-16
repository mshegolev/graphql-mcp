"""FastAPI inbound adapter — thin delegation to GraphQLClient.

Run: uvicorn graphql_mcp.adapters.inbound.rest:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import math
import time as _time
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from graphql_mcp.adapters.inbound.lib import GraphQLClient

if TYPE_CHECKING:
    from starlette.types import ASGIApp
from graphql_mcp.adapters.inbound.mcp_http import create_mcp_http_app
from graphql_mcp.adapters.outbound.query_guard import check_query_depth
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.errors import MutationGuardError, QueryDepthError, SchemaResolutionError

# ---------------------------------------------------------------------------
# Header forwarding
# ---------------------------------------------------------------------------

_FORWARDED_HEADERS = ("authorization", "x-user-id", "x-roles")


def _extract_forwarded_headers(request: Request) -> dict[str, str]:
    """Extract allowed inbound headers to forward to upstream GraphQL."""
    return {k: v for k, v in request.headers.items() if k.lower() in _FORWARDED_HEADERS}


# ---------------------------------------------------------------------------
# Rate limiter middleware
# ---------------------------------------------------------------------------

_WINDOW_MAP = {"second": 1, "minute": 60, "hour": 3600}
_EXEMPT_PATHS = {"/health", "/ready"}


def _parse_rate_limit(rate_limit: str) -> tuple[int, int]:
    """Parse ``"100/minute"`` into ``(max_requests, window_seconds)``."""
    parts = rate_limit.split("/", 1)
    if len(parts) != 2:
        return 100, 60  # safe default
    try:
        max_requests = int(parts[0])
    except ValueError:
        max_requests = 100
    window_seconds = _WINDOW_MAP.get(parts[1].strip().lower(), 60)
    return max_requests, window_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP-based sliding-window rate limiter.

    Reads ``GRAPHQL_RATE_LIMIT`` from config on init. Skips health/ready
    endpoints. Returns 429 + ``Retry-After`` when limit is exceeded.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        config = GraphQLConfig()
        self._max_requests, self._window_seconds = _parse_rate_limit(config.rate_limit)
        self._windows: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Skip health/ready probes
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = _time.time()

        # Prune expired timestamps
        window = self._windows.setdefault(client_ip, [])
        cutoff = now - self._window_seconds
        self._windows[client_ip] = window = [t for t in window if t > cutoff]

        if len(window) >= self._max_requests:
            oldest = window[0] if window else now
            remaining = math.ceil(self._window_seconds - (now - oldest))
            return JSONResponse(
                status_code=429,
                content={"error": "rate limit exceeded"},
                headers={"Retry-After": str(max(remaining, 1))},
            )

        window.append(now)
        return await call_next(request)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="graphql-mcp", version="0.1.0")
app.add_middleware(RateLimitMiddleware)
app.mount("/mcp", create_mcp_http_app())

# OTEL: auto-instrument FastAPI if opentelemetry is available
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)
except ImportError:
    pass  # OTEL not installed — no-op

_client: GraphQLClient | None = None


def _get_client() -> GraphQLClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = GraphQLClient.from_env()
    return _client


def set_client(client: GraphQLClient) -> None:
    """Override the global client (for testing)."""
    global _client  # noqa: PLW0603
    _client = client


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(SchemaResolutionError)
async def schema_resolution_handler(request: Request, exc: SchemaResolutionError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": "schema unavailable", "detail": str(exc)},
    )


@app.exception_handler(QueryDepthError)
async def query_depth_handler(request: Request, exc: QueryDepthError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "depth": exc.depth, "max_depth": exc.max_depth},
    )


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    """Readiness probe: 200 when schema source is resolvable, 503 otherwise."""
    client = _get_client()
    try:
        _ = client.schema  # triggers SchemaService.resolve()
        return JSONResponse(status_code=200, content={"status": "ready"})
    except SchemaResolutionError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": "schema resolution failed"},
        )


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    query: str
    variables: dict[str, Any] | None = None


class EntitiesRequest(BaseModel):
    representations: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/graphql/query")
def graphql_query(req: QueryRequest, request: Request) -> dict[str, Any]:
    config = GraphQLConfig()
    check_query_depth(req.query, config.max_query_depth)
    client = _get_client()
    # Set audit context for this request
    client._audit_caller_ip = request.client.host if request.client else "unknown"
    client._audit_caller_identity = request.headers.get("x-user-id", "anonymous")
    forwarded = _extract_forwarded_headers(request)
    try:
        result = client.query(req.query, req.variables, extra_headers=forwarded or None)
    except MutationGuardError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "data": result.data,
        "errors": result.errors,
        "error_class": result.error_class.value,
    }


@app.get("/graphql/introspect")
def graphql_introspect() -> dict[str, Any]:
    client = _get_client()
    summary = client.introspect()
    return summary.model_dump()


@app.get("/graphql/type/{type_name}")
def graphql_describe_type(type_name: str) -> dict[str, Any]:
    client = _get_client()
    info = client.describe_type(type_name)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Type '{type_name}' not found")
    return info.model_dump()


@app.get("/graphql/subgraphs")
def graphql_list_subgraphs() -> list[dict[str, Any]]:
    client = _get_client()
    return [s.model_dump() for s in client.list_subgraphs()]


@app.post("/graphql/raw")
def graphql_raw(body: dict[str, Any], request: Request) -> dict[str, Any]:
    """Send an arbitrary GraphQL POST body and return typed result."""
    config = GraphQLConfig()
    query_str = body.get("query")
    if isinstance(query_str, str):
        check_query_depth(query_str, config.max_query_depth)
    client = _get_client()
    # Set audit context for this request
    client._audit_caller_ip = request.client.host if request.client else "unknown"
    client._audit_caller_identity = request.headers.get("x-user-id", "anonymous")
    forwarded = _extract_forwarded_headers(request)
    try:
        result = client.raw(body, extra_headers=forwarded or None)
    except MutationGuardError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "data": result.data,
        "errors": result.errors,
        "error_class": result.error_class.value,
    }


@app.post("/graphql/entities")
def graphql_entities(req: EntitiesRequest, request: Request) -> dict[str, Any]:
    """Resolve federation entities via _entities pass-through."""
    client = _get_client()
    # Set audit context for this request
    client._audit_caller_ip = request.client.host if request.client else "unknown"
    client._audit_caller_identity = request.headers.get("x-user-id", "anonymous")
    forwarded = _extract_forwarded_headers(request)
    result = client.entities(req.representations, extra_headers=forwarded or None)
    return {
        "data": result.data,
        "errors": result.errors,
        "error_class": result.error_class.value,
    }


@app.post("/graphql/refresh")
def graphql_refresh() -> dict[str, str]:
    client = _get_client()
    client.refresh_schema()
    return {"status": "refreshed"}
