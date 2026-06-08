"""FastAPI inbound adapter — thin delegation to GraphQLClient.

Run: uvicorn graphql_mcp.adapters.inbound.rest:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.domain.errors import MutationGuardError

app = FastAPI(title="graphql-mcp", version="0.1.0")

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class QueryRequest(BaseModel):
    query: str
    variables: dict[str, Any] | None = None


@app.post("/graphql/query")
def graphql_query(req: QueryRequest) -> dict[str, Any]:
    client = _get_client()
    try:
        result = client.query(req.query, req.variables)
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
def graphql_raw(body: dict[str, Any]) -> dict[str, Any]:
    """Send an arbitrary GraphQL POST body and return typed result."""
    client = _get_client()
    try:
        result = client.raw(body)
    except MutationGuardError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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
