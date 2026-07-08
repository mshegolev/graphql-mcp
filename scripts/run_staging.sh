#!/usr/bin/env bash
# Run generic-graphql-mcp locally against the EORD staging federation gateway.
#
# Config (endpoint / proxy bypass / SSL) mirrors the EORD integration-tests
# pytest.ini [env] block. Credentials are NEVER stored here — supply ONE of:
#   A) ISSO_CLIENT_SECRET + ISSO_PASSWORD  -> a fresh ISSO (Keycloak) token is fetched
#   B) GRAPHQL_BEARER_TOKEN                 -> use an already-issued bearer token
#
# Usage: scripts/run_staging.sh [serve|stdio|smoke]   (default: smoke)
set -euo pipefail

MODE="${1:-smoke}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
[ -x "$HERE/.venv/bin/python" ] && PY="$HERE/.venv/bin/python"

# ---- staging config (from integration-tests/pytest.ini) ----
export GRAPHQL_ENDPOINT="${GRAPHQL_ENDPOINT:-https://gql.enp-stage.mts-corp.ru/}"
export GRAPHQL_SSL_VERIFY="${GRAPHQL_SSL_VERIFY:-false}"
export GRAPHQL_SCHEMA_SOURCE="${GRAPHQL_SCHEMA_SOURCE:-introspection}"
export GRAPHQL_ALLOW_MUTATIONS="${GRAPHQL_ALLOW_MUTATIONS:-false}"
export GRAPHQL_HTTP_HOST="${GRAPHQL_HTTP_HOST:-127.0.0.1}"
export GRAPHQL_HTTP_PORT="${GRAPHQL_HTTP_PORT:-8123}"
# internal MTS hosts sit behind a proxy that blocks them — bypass it
export NO_PROXY="*"; export no_proxy="*"; export HTTPS_PROXY=""; export https_proxy=""

# ---- obtain bearer token (never persisted) ----
if [ -z "${GRAPHQL_BEARER_TOKEN:-}" ]; then
  if [ -n "${ISSO_CLIENT_SECRET:-}" ] && [ -n "${ISSO_PASSWORD:-}" ]; then
    echo "[auth] fetching ISSO token (client_id=${ISSO_CLIENT_ID:-eordui-stage})..." >&2
    GRAPHQL_BEARER_TOKEN=$(curl -sk --noproxy '*' -X POST \
      "${ISSO_TOKEN_URL:-https://isso-dev.mts.ru/auth/realms/mts/protocol/openid-connect/token}" \
      -d grant_type=password \
      -d client_id="${ISSO_CLIENT_ID:-eordui-stage}" \
      -d client_secret="$ISSO_CLIENT_SECRET" \
      -d username="${ISSO_USERNAME:-sa0000eord}" \
      -d password="$ISSO_PASSWORD" \
      | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))')
    if [ -z "$GRAPHQL_BEARER_TOKEN" ]; then
      echo "[auth] FAILED to obtain ISSO token" >&2; exit 1
    fi
    export GRAPHQL_BEARER_TOKEN
    echo "[auth] token acquired (len=${#GRAPHQL_BEARER_TOKEN})" >&2
  else
    echo "[auth] no GRAPHQL_BEARER_TOKEN and no ISSO_CLIENT_SECRET/ISSO_PASSWORD;" >&2
    echo "[auth] running unauthenticated — the staging gateway will return 401." >&2
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
    exec "$PY" "$HERE/scripts/staging_smoke.py"
    ;;
  *)
    echo "usage: $0 [serve|stdio|smoke]" >&2; exit 2 ;;
esac
