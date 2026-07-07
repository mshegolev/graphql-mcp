"""Click CLI inbound adapter — ad-hoc queries from terminal.

Usage: generic-graphql-mcp query '{ __typename }'
       generic-graphql-mcp introspect
       generic-graphql-mcp describe-type User
       generic-graphql-mcp list-subgraphs
       generic-graphql-mcp refresh
       generic-graphql-mcp subscribe 'subscription { events { id } }'
       generic-graphql-mcp serve [--host HOST] [--port PORT]
"""

from __future__ import annotations

import json
import sys

import click


@click.group()
def main() -> None:
    """generic-graphql-mcp — Generic read-only GraphQL client."""


@main.command()
@click.argument("query_string")
@click.option("--variables", "-v", default=None, help="JSON string of variables")
def query(query_string: str, variables: str | None) -> None:
    """Execute a GraphQL query."""
    from generic_graphql_mcp import GraphQLClient
    from generic_graphql_mcp.domain.errors import MutationGuardError

    client = GraphQLClient.from_env()
    vars_dict = json.loads(variables) if variables else None
    try:
        result = client.query(query_string, vars_dict)
    except MutationGuardError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(json.dumps(result.model_dump(), indent=2, default=str))


@main.command()
def introspect() -> None:
    """Show schema summary (Query fields and types)."""
    from generic_graphql_mcp import GraphQLClient
    from generic_graphql_mcp.domain.errors import SchemaResolutionError

    client = GraphQLClient.from_env()
    try:
        summary = client.introspect()
    except SchemaResolutionError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(json.dumps(summary.model_dump(), indent=2, default=str))


@main.command("describe-type")
@click.argument("type_name")
def describe_type(type_name: str) -> None:
    """Describe a GraphQL type (fields, args, subgraph)."""
    from generic_graphql_mcp import GraphQLClient
    from generic_graphql_mcp.domain.errors import SchemaResolutionError

    client = GraphQLClient.from_env()
    try:
        info = client.describe_type(type_name)
    except SchemaResolutionError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    if info is None:
        click.echo(f"Type '{type_name}' not found", err=True)
        sys.exit(1)
    click.echo(json.dumps(info.model_dump(), indent=2, default=str))


@main.command("list-subgraphs")
def list_subgraphs() -> None:
    """List federation subgraphs."""
    from generic_graphql_mcp import GraphQLClient
    from generic_graphql_mcp.domain.errors import SchemaResolutionError

    client = GraphQLClient.from_env()
    try:
        subgraphs = client.list_subgraphs()
    except SchemaResolutionError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(json.dumps([s.model_dump() for s in subgraphs], indent=2, default=str))


@main.command()
@click.argument("body_json")
def raw(body_json: str) -> None:
    """Send an arbitrary GraphQL POST body (JSON string)."""
    from generic_graphql_mcp import GraphQLClient
    from generic_graphql_mcp.domain.errors import MutationGuardError

    client = GraphQLClient.from_env()
    body = json.loads(body_json)
    try:
        result = client.raw(body)
    except MutationGuardError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(json.dumps(result.model_dump(), indent=2, default=str))


@main.command()
@click.argument("representations_json")
def entities(representations_json: str) -> None:
    """Resolve federation entities via _entities pass-through (JSON array of representations)."""
    from generic_graphql_mcp import GraphQLClient

    client = GraphQLClient.from_env()
    reps = json.loads(representations_json)
    result = client.entities(reps)
    click.echo(json.dumps(result.model_dump(), indent=2, default=str))


@main.command()
@click.argument("query_string")
@click.option("--variables", "-v", default=None, help="JSON string of variables")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "table"]), help="Output format")
def subscribe(query_string: str, variables: str | None, format: str) -> None:
    """Subscribe to a GraphQL subscription and stream results."""
    try:
        from generic_graphql_mcp import GraphQLClient
        from generic_graphql_mcp.domain.errors import MutationGuardError
    except ImportError:
        click.echo(
            "Error: websockets is required for subscription support. "
            "Install with: pip install generic-graphql-mcp[subscriptions]",
            err=True,
        )
        sys.exit(1)

    client = GraphQLClient.from_env()
    vars_dict = json.loads(variables) if variables else None

    try:
        for result in client.subscribe(query_string, vars_dict):
            if format == "table":
                # Simple table format for common case
                if result.data:
                    for key, value in result.data.items():
                        click.echo(f"{key}: {json.dumps(value, default=str)}")
                if result.errors:
                    click.echo(f"Errors: {result.errors}")
            else:
                # JSON format
                click.echo(json.dumps(result.model_dump(), default=str))

            # Flush output to ensure it's visible immediately
            sys.stdout.flush()

    except MutationGuardError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nSubscription stopped.", err=True)
        sys.exit(0)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
def refresh() -> None:
    """Clear schema cache, forcing re-fetch."""
    from generic_graphql_mcp import GraphQLClient

    client = GraphQLClient.from_env()
    client.refresh_schema()
    click.echo(json.dumps({"status": "refreshed"}))


@main.command()
@click.option("--host", default=None, help="Bind host (overrides GRAPHQL_HTTP_HOST, default 0.0.0.0)")
@click.option("--port", default=None, type=int, help="Bind port (overrides GRAPHQL_HTTP_PORT, default 8000)")
def serve(host: str | None, port: int | None) -> None:
    """Start the FastAPI server with REST + MCP-over-HTTP endpoints."""
    import uvicorn

    from generic_graphql_mcp.adapters.outbound.otel_bootstrap import init_otel
    from generic_graphql_mcp.config import GraphQLConfig

    init_otel()  # Configure OTEL from env vars (no-op if packages absent)

    config = GraphQLConfig()
    bind_host = host or config.http_host
    bind_port = port or config.http_port
    uvicorn.run(
        "generic_graphql_mcp.adapters.inbound.rest:app",
        host=bind_host,
        port=bind_port,
    )


if __name__ == "__main__":
    main()
