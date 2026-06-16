"""Minimal mock GraphQL server for integration testing.

Uses only stdlib + graphql-core to serve a simple schema.
Designed to be run as a standalone script or inside a Docker container.

Usage:
    python -m tests.integration.mock_server
    # or
    python tests/integration/mock_server.py

Serves on 0.0.0.0:4000 by default. Override with:
    MOCK_SERVER_HOST=127.0.0.1 MOCK_SERVER_PORT=4001 python tests/integration/mock_server.py
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    graphql_sync,
)

# ---- Schema definition ----

UserType = GraphQLObjectType(
    "User",
    lambda: {
        "id": GraphQLField(GraphQLNonNull(GraphQLString)),
        "name": GraphQLField(GraphQLNonNull(GraphQLString)),
        "email": GraphQLField(GraphQLString),
    },
)

MOCK_USERS = [
    {"id": "1", "name": "Alice", "email": "alice@example.com"},
    {"id": "2", "name": "Bob", "email": "bob@example.com"},
    {"id": "3", "name": "Charlie", "email": "charlie@example.com"},
]


def resolve_hello(_root, _info):
    return "Hello from mock GraphQL server!"


def resolve_users(_root, _info):
    return MOCK_USERS


def resolve_user(_root, _info, id):
    return next((u for u in MOCK_USERS if u["id"] == id), None)


QueryType = GraphQLObjectType(
    "Query",
    {
        "hello": GraphQLField(GraphQLString, resolve=resolve_hello),
        "users": GraphQLField(
            GraphQLList(UserType),
            resolve=resolve_users,
        ),
        "user": GraphQLField(
            UserType,
            args={"id": GraphQLArgument(GraphQLNonNull(GraphQLString))},
            resolve=resolve_user,
        ),
    },
)

schema = GraphQLSchema(query=QueryType)


# ---- HTTP handler ----


class GraphQLHandler(BaseHTTPRequestHandler):
    """Handle POST /graphql requests."""

    def do_POST(self):
        if self.path.rstrip("/") != "/graphql":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        query = data.get("query", "")
        variables = data.get("variables")
        operation_name = data.get("operationName")

        result = graphql_sync(
            schema,
            query,
            variable_values=variables,
            operation_name=operation_name,
        )

        response = {}
        if result.data is not None:
            response["data"] = result.data
        if result.errors:
            response["errors"] = [{"message": str(e), "locations": e.locations, "path": e.path} for e in result.errors]

        response_body = json.dumps(response).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        """Health check endpoint."""
        if self.path.rstrip("/") == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            body = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        """Suppress request logging unless DEBUG is set."""
        if os.environ.get("DEBUG"):
            super().log_message(format, *args)


def main():
    host = os.environ.get("MOCK_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MOCK_SERVER_PORT", "4000"))

    server = HTTPServer((host, port), GraphQLHandler)
    print(f"Mock GraphQL server running on http://{host}:{port}/graphql")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server.")
        server.shutdown()


if __name__ == "__main__":
    main()
