#!/usr/bin/env bash
# Run generic-graphql-mcp locally against any GraphQL endpoint.
#
# Required:
#   GRAPHQL_ENDPOINT          e.g. https://graphql.example.com/
# Auth (optional) - supply ONE of (credentials are never stored here):
#   A) OAUTH_TOKEN_URL + OAUTH_CLIENT_ID + OAUTH_CLIENT_SECRET + OAUTH_USERNAME + OAUTH_PASSWORD
#        -> a fresh token is fetched via the OAuth2 password grant
#        (e.g. OAUTH_TOKEN_URL=https://auth.example.com/realms/acme/protocol/openid-connect/token,
#              OAUTH_CLIENT_ID=my-client, OAUTH_USERNAME=acme-user)
#   B) GRAPHQL_BEARER_TOKEN   -> use an already-issued bearer token
# Optional:
#   GRAPHQL_NO_PROXY=true     -> bypass any HTTP(S) proxy for this run
#
# Usage: scripts/run_local.sh [serve|stdio|smoke]   (default: smoke)
set -euo pipefail

MODE="${1:-smoke}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
[ -x "$HERE/.venv/bin/python" ] && PY="$HERE/.venv/bin/python"

: "${GRAPHQL_ENDPOINT:?set GRAPHQL_ENDPOINT, e.g. https://graphql.example.com/}"
export GRAPHQL_ENDPOINT
export GRAPHQL_SCHEMA_SOURCE="${GRAPHQL_SCHEMA_SOURCE:-introspection}"
export GRAPHQL_ALLOW_MUTATIONS="${GRAPHQL_ALLOW_MUTATIONS:-false}"
export GRAPHQL_HTTP_HOST="${GRAPHQL_HTTP_HOST:-127.0.0.1}"
export GRAPHQL_HTTP_PORT="${GRAPHQL_HTTP_PORT:-8123}"
if [ "${GRAPHQL_NO_PROXY:-false}" = "true" ]; then
  export NO_PROXY="*"; export no_proxy="*"; export HTTPS_PROXY=""; export https_proxy=""
fi

# ---- obtain bearer token (never persisted) ----
if [ -z "${GRAPHQL_BEARER_TOKEN:-}" ]; then
  if [ -n "${OAUTH_TOKEN_URL:-}" ] && [ -n "${OAUTH_CLIENT_ID:-}" ] \
     && [ -n "${OAUTH_CLIENT_SECRET:-}" ] && [ -n "${OAUTH_USERNAME:-}" ] \
     && [ -n "${OAUTH_PASSWORD:-}" ]; then
    echo "[auth] fetching OAuth2 token (client_id=${OAUTH_CLIENT_ID})..." >&2
    GRAPHQL_BEARER_TOKEN=$(curl -s -X POST "$OAUTH_TOKEN_URL" \
      -d grant_type=password \
      -d client_id="$OAUTH_CLIENT_ID" \
      -d client_secret="$OAUTH_CLIENT_SECRET" \
      -d username="$OAUTH_USERNAME" \
      -d password="$OAUTH_PASSWORD" \
      | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))')
    if [ -z "$GRAPHQL_BEARER_TOKEN" ]; then
      echo "[auth] FAILED to obtain OAuth2 token" >&2; exit 1
    fi
    export GRAPHQL_BEARER_TOKEN
    echo "[auth] token acquired (len=${#GRAPHQL_BEARER_TOKEN})" >&2
  else
    echo "[auth] no GRAPHQL_BEARER_TOKEN and no complete OAUTH_* credentials;" >&2
    echo "[auth] running unauthenticated - an authenticated endpoint will return 401." >&2
  fi
fi

cd "$HERE"
case "$MODE" in
  serve)
    exec "$PY" -m generic_graphql_mcp.adapters.inbound.cli serve \
      --host "$GRAPHQL_HTTP_HOST" --port "$GRAPHQL_HTTP_PORT"
    ;;
  stdio)
    exec "$PY" -m generic_graphql_mcp.adapters.inbound.mcp_stdio
    ;;
  smoke)
    exec "$PY" "$HERE/scripts/smoke_check.py"
    ;;
  *)
    echo "usage: $0 [serve|stdio|smoke]" >&2; exit 2 ;;
esac
