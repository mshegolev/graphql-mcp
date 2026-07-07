"""OAuth2 client_credentials token manager with automatic refresh."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class _TokenInfo:
    access_token: str
    expires_at: float  # monotonic time


class OAuth2TokenManager:
    """Thread-safe OAuth2 client_credentials token cache with auto-refresh.

    Fetches a new token when the current one is expired or within
    ``refresh_margin_seconds`` of expiry.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scopes: str = "",
        refresh_margin_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes
        self._margin = refresh_margin_seconds
        self._lock = threading.Lock()
        self._token: _TokenInfo | None = None
        self._http = http_client or httpx.Client(timeout=10.0)
        self._owns_http = http_client is None

    def get_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        with self._lock:
            if self._token is None or time.monotonic() >= (self._token.expires_at - self._margin):
                self._refresh()
            assert self._token is not None
            return self._token.access_token

    def _refresh(self) -> None:
        """Fetch a new token from the token endpoint."""
        data: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        if self._scopes:
            data["scope"] = self._scopes
        try:
            resp = self._http.post(self._token_url, data=data)
            resp.raise_for_status()
            body = resp.json()
            expires_in = float(body.get("expires_in", 3600))
            self._token = _TokenInfo(
                access_token=body["access_token"],
                expires_at=time.monotonic() + expires_in,
            )
            logger.debug("OAuth2 token refreshed, expires_in=%s", expires_in)
        except Exception:
            logger.exception("OAuth2 token refresh failed")
            raise

    def close(self) -> None:
        """Release HTTP resources."""
        if self._owns_http:
            self._http.close()


class AsyncOAuth2TokenManager:
    """Async OAuth2 client_credentials token cache with auto-refresh.

    Async counterpart to :class:`OAuth2TokenManager`.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scopes: str = "",
        refresh_margin_seconds: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes
        self._margin = refresh_margin_seconds
        self._lock = asyncio.Lock()
        self._token: _TokenInfo | None = None
        self._http = http_client or httpx.AsyncClient(timeout=10.0)
        self._owns_http = http_client is None

    async def get_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        async with self._lock:
            if self._token is None or time.monotonic() >= (self._token.expires_at - self._margin):
                await self._refresh()
            assert self._token is not None
            return self._token.access_token

    async def _refresh(self) -> None:
        """Fetch a new token from the token endpoint."""
        data: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        if self._scopes:
            data["scope"] = self._scopes
        try:
            resp = await self._http.post(self._token_url, data=data)
            resp.raise_for_status()
            body = resp.json()
            expires_in = float(body.get("expires_in", 3600))
            self._token = _TokenInfo(
                access_token=body["access_token"],
                expires_at=time.monotonic() + expires_in,
            )
            logger.debug("Async OAuth2 token refreshed, expires_in=%s", expires_in)
        except Exception:
            logger.exception("Async OAuth2 token refresh failed")
            raise

    async def close(self) -> None:
        """Release HTTP resources."""
        if self._owns_http:
            await self._http.aclose()
