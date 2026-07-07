"""Subscription rate limiting logic for generic-graphql-mcp.

Provides IP-based rate limiting for subscription connections to prevent
resource exhaustion from too many concurrent or frequent subscription requests.
"""

from __future__ import annotations

import math
import time as _time
from typing import Dict, List

from generic_graphql_mcp.config import GraphQLConfig

# Map rate limit window names to seconds
_WINDOW_MAP = {"second": 1, "minute": 60, "hour": 3600}


def _parse_rate_limit(rate_limit: str) -> tuple[int, int]:
    """Parse ``"10/minute"`` into ``(max_requests, window_seconds)``."""
    parts = rate_limit.split("/", 1)
    if len(parts) != 2:
        return 10, 60  # safe default
    try:
        max_requests = int(parts[0])
    except ValueError:
        max_requests = 10
    window_seconds = _WINDOW_MAP.get(parts[1].strip().lower(), 60)
    return max_requests, window_seconds


class SubscriptionRateLimiter:
    """IP-based rate limiter for subscription connections.

    Tracks both connection rate and concurrent connection count per IP.
    """

    def __init__(self) -> None:
        config = GraphQLConfig()
        self._max_connections, self._window_seconds = _parse_rate_limit(config.subscription_rate_limit)
        self._max_concurrent = config.max_concurrent_subscriptions
        self._connection_windows: Dict[str, List[float]] = {}  # IP -> timestamps
        self._concurrent_counts: Dict[str, int] = {}  # IP -> current connections

    def check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        """Check if client can create a new subscription connection.

        Returns:
            Tuple of (allowed: bool, retry_after: int seconds).
            If allowed is False, retry_after indicates when to try again.
        """
        now = _time.time()

        # Prune expired timestamps
        window = self._connection_windows.setdefault(client_ip, [])
        cutoff = now - self._window_seconds
        self._connection_windows[client_ip] = window = [t for t in window if t > cutoff]

        # Check rate limit
        if len(window) >= self._max_connections:
            oldest = window[0] if window else now
            remaining = math.ceil(self._window_seconds - (now - oldest))
            return False, max(remaining, 1)

        # Check concurrent limit
        current_concurrent = self._concurrent_counts.get(client_ip, 0)
        if current_concurrent >= self._max_concurrent:
            return False, 1  # Try again shortly

        return True, 0

    def increment_connection(self, client_ip: str) -> None:
        """Record a new subscription connection for the client."""
        now = _time.time()
        self._connection_windows.setdefault(client_ip, []).append(now)
        self._concurrent_counts[client_ip] = self._concurrent_counts.get(client_ip, 0) + 1

    def decrement_connection(self, client_ip: str) -> None:
        """Record that a subscription connection has ended."""
        current = self._concurrent_counts.get(client_ip, 0)
        if current > 0:
            self._concurrent_counts[client_ip] = current - 1
        # Don't remove from connection windows - those timestamps are historical
