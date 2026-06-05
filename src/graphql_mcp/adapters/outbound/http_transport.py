from __future__ import annotations

import logging
from typing import Any

import httpx
import orjson

from graphql_mcp.domain.models import ErrorClass, QueryResult

logger = logging.getLogger(__name__)


class HttpTransport:
    """Outbound adapter: httpx-based GraphQL transport."""

    def __init__(
        self,
        endpoint: str,
        bearer_token: str = "",
        timeout: float = 30.0,
        ssl_verify: bool = True,
        headers: dict[str, str] | None = None,
    ) -> None:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if bearer_token:
            h["Authorization"] = f"Bearer {bearer_token}"
        if headers:
            h.update(headers)

        self._client = httpx.Client(
            base_url=endpoint,
            headers=h,
            timeout=httpx.Timeout(timeout, connect=min(timeout, 10.0)),
            verify=ssl_verify,
        )

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> QueryResult:
        body: dict[str, Any] = {"query": query}
        if variables:
            body["variables"] = variables
        return self.post_raw(body)

    def post_raw(self, body: dict[str, Any]) -> QueryResult:
        try:
            response = self._client.post("", content=orjson.dumps(body))
        except (httpx.HTTPError, httpx.StreamError, OSError) as exc:
            logger.warning("Transport error: %s", exc)
            return QueryResult(
                data=None,
                errors=[{"message": f"Transport error: {exc}"}],
                error_class=ErrorClass.TRANSPORT,
            )

        if response.status_code != 200:
            return QueryResult(
                data=None,
                errors=[{"message": f"HTTP {response.status_code}: {response.text[:500]}"}],
                error_class=ErrorClass.TRANSPORT,
            )

        try:
            result = orjson.loads(response.content)
        except (orjson.JSONDecodeError, ValueError) as exc:
            return QueryResult(
                data=None,
                errors=[{"message": f"Invalid JSON response: {exc}"}],
                error_class=ErrorClass.TRANSPORT,
            )

        data = result.get("data")
        errors = result.get("errors", [])
        error_class = ErrorClass.GRAPHQL if errors else ErrorClass.OK

        return QueryResult(data=data, errors=errors, error_class=error_class)

    def close(self) -> None:
        self._client.close()
