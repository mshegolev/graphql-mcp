from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphQLConfig(BaseSettings):
    """Environment-driven configuration for generic-graphql-mcp.

    All env vars are prefixed with GRAPHQL_ (e.g., GRAPHQL_ENDPOINT).
    """

    model_config = SettingsConfigDict(
        env_prefix="GRAPHQL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Connection
    endpoint: str = ""
    bearer_token: str = ""
    timeout: int = 30
    ssl_verify: bool = True
    noproxy: str = ""

    # Schema source selection
    schema_source: str = "auto"  # auto|gitlab|introspection|federation|sdl_file
    schema_sdl: str = ""  # path to local SDL file
    schema_ttl: int = 300  # seconds

    # GitLab schema source
    schema_gitlab_url: str = ""
    schema_gitlab_project_id: str = ""
    schema_gitlab_file_path: str = ""
    schema_gitlab_ref: str = "HEAD"
    gitlab_token: str = ""

    # Behavior
    allow_mutations: bool = False

    # HTTP server
    http_host: str = "0.0.0.0"
    http_port: int = 8000

    # Federation
    supergraph_source: str = "auto"  # auto|off — controls list_subgraphs behavior

    # Security
    max_query_depth: int = 10  # GRAPHQL_MAX_QUERY_DEPTH
    rate_limit: str = "100/minute"  # GRAPHQL_RATE_LIMIT — "{count}/{window}" where window ∈ {second, minute, hour}
    audit_log: bool = False  # GRAPHQL_AUDIT_LOG — used by Plan 03

    # mTLS
    client_cert: str = ""  # GRAPHQL_CLIENT_CERT — path to client certificate PEM
    client_key: str = ""  # GRAPHQL_CLIENT_KEY — path to client private key PEM
    ca_bundle: str = ""  # GRAPHQL_CA_BUNDLE — path to CA bundle PEM

    # OAuth2 client_credentials
    oauth2_token_url: str = ""  # GRAPHQL_OAUTH2_TOKEN_URL
    oauth2_client_id: str = ""  # GRAPHQL_OAUTH2_CLIENT_ID
    oauth2_client_secret: str = ""  # GRAPHQL_OAUTH2_CLIENT_SECRET
    oauth2_scopes: str = ""  # GRAPHQL_OAUTH2_SCOPES — space-separated

    # Subscriptions
    subscription_endpoint: str = ""  # GRAPHQL_SUBSCRIPTION_ENDPOINT — ws:// or wss:// URL for upstream subscription WS
    subscription_queue_size: int = 128  # GRAPHQL_SUBSCRIPTION_QUEUE_SIZE — bounded async queue for backpressure
    subscription_rate_limit: str = (
        "10/minute"  # GRAPHQL_SUBSCRIPTION_RATE_LIMIT — "{count}/{window}" for subscription connections per IP
    )
    max_concurrent_subscriptions: int = (
        100  # GRAPHQL_MAX_CONCURRENT_SUBSCRIPTIONS — max concurrent subscription connections per IP
    )
