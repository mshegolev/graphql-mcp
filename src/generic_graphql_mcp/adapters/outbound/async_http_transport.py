from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from generic_graphql_mcp.adapters.outbound.codec_factory import get_codec
from generic_graphql_mcp.domain.models import ErrorClass, QueryResult

if TYPE_CHECKING:
    import ssl

    from generic_graphql_mcp.adapters.outbound.oauth2 import AsyncOAuth2TokenManager
    from generic_graphql_mcp.ports.json_codec import JsonCodec

logger = logging.getLogger(__name__)


class AsyncHttpTransport:
    """Outbound adapter: httpx-based async GraphQL transport."""

    def __init__(
        self,
        endpoint: str,
        bearer_token: str = "",
        timeout: float = 30.0,
        ssl_verify: bool = True,
        headers: dict[str, str] | None = None,
        codec: JsonCodec | None = None,
        ssl_context: ssl.SSLContext | None = None,
        oauth2: AsyncOAuth2TokenManager | None = None,
    ) -> None:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if bearer_token:
            h["Authorization"] = f"Bearer {bearer_token}"
        if headers:
            h.update(headers)

        self._codec = codec or get_codec()
        self._oauth2 = oauth2

        # ssl_context takes precedence over ssl_verify when provided
        verify: ssl.SSLContext | bool = ssl_context if ssl_context is not None else ssl_verify

        self._client = httpx.AsyncClient(
            base_url=endpoint,
            headers=h,
            timeout=httpx.Timeout(timeout, connect=min(timeout, 10.0)),
            verify=verify,
        )

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> QueryResult:
        body: dict[str, Any] = {"query": query}
        if variables:
            body["variables"] = variables
        return await self.post_raw(body, extra_headers=extra_headers)

    async def post_raw(self, body: dict[str, Any], extra_headers: dict[str, str] | None = None) -> QueryResult:
        merged_headers = dict(extra_headers) if extra_headers else {}
        if self._oauth2 is not None:
            merged_headers["Authorization"] = f"Bearer {await self._oauth2.get_token()}"
        try:
            response = await self._client.post("", content=self._codec.encode(body), headers=merged_headers or None)
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

    async def close(self) -> None:
        await self._client.aclose()
        if self._oauth2 is not None:
            await self._oauth2.close()
