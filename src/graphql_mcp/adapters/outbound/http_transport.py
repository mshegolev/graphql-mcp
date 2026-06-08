from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from graphql_mcp.adapters.outbound.codec_factory import get_codec
from graphql_mcp.domain.models import ErrorClass, QueryResult

if TYPE_CHECKING:
    from graphql_mcp.ports.json_codec import JsonCodec

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
        codec: JsonCodec | None = None,
    ) -> None:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if bearer_token:
            h["Authorization"] = f"Bearer {bearer_token}"
        if headers:
            h.update(headers)

        self._codec = codec or get_codec()

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
            response = self._client.post("", content=self._codec.encode(body))
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
            result = self._codec.decode(response.content)
        except (ValueError, TypeError) as exc:
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
