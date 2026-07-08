#!/usr/bin/env python3
"""Staging connectivity smoke check for generic-graphql-mcp.

Builds a GraphQLClient from the GRAPHQL_* environment (see scripts/run_staging.sh)
and verifies live connectivity to the EORD staging federation gateway:

  1. introspect() returns at least one Query root field, and
  2. list_subgraphs() returns at least one named federation subgraph.

Exit code 0 on success, 1 on any failure. Secrets are never printed.

Run via: scripts/run_staging.sh smoke   (or set GRAPHQL_* + run directly)
"""

from __future__ import annotations

import sys

from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.domain.errors import SchemaResolutionError


def main() -> int:
    client = GraphQLClient.from_env()

    # 1) introspection — Query root fields
    try:
        summary = client.introspect()
    except SchemaResolutionError as exc:
        print(f"FAIL introspect: schema unavailable — {exc}", file=sys.stderr)
        print(
            "     (401 from the gateway means no/expired bearer token — set "
            "ISSO_CLIENT_SECRET/ISSO_PASSWORD or GRAPHQL_BEARER_TOKEN)",
            file=sys.stderr,
        )
        return 1

    n_fields = len(summary.query_fields)
    if n_fields == 0:
        print("FAIL introspect: schema resolved but exposes no Query fields", file=sys.stderr)
        return 1
    print(f"OK  introspect: {n_fields} Query fields, {len(summary.types)} types")

    # 2) federation subgraphs
    try:
        subgraphs = client.list_subgraphs()
    except SchemaResolutionError as exc:
        print(f"FAIL list_subgraphs: {exc}", file=sys.stderr)
        return 1

    if not subgraphs:
        print("FAIL list_subgraphs: no federation subgraphs returned", file=sys.stderr)
        return 1
    names = ", ".join(sorted(s.name for s in subgraphs)[:8])
    print(f"OK  list_subgraphs: {len(subgraphs)} subgraphs — {names}")

    print("staging smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
