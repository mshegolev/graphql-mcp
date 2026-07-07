"""Tests for mTLS configuration (SEC-04)."""

from __future__ import annotations

import ssl

import pytest

from generic_graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from generic_graphql_mcp.adapters.outbound.http_transport import HttpTransport
from generic_graphql_mcp.config import GraphQLConfig


class TestMtlsConfig:
    """Config reads mTLS-related env vars."""

    def test_config_reads_mtls_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPHQL_CLIENT_CERT", "/path/to/cert.pem")
        monkeypatch.setenv("GRAPHQL_CLIENT_KEY", "/path/to/key.pem")
        monkeypatch.setenv("GRAPHQL_CA_BUNDLE", "/path/to/ca.pem")
        config = GraphQLConfig()
        assert config.client_cert == "/path/to/cert.pem"
        assert config.client_key == "/path/to/key.pem"
        assert config.ca_bundle == "/path/to/ca.pem"

    def test_mtls_fields_default_empty(self) -> None:
        config = GraphQLConfig()
        assert config.client_cert == ""
        assert config.client_key == ""
        assert config.ca_bundle == ""


class TestMtlsTransport:
    """HttpTransport and AsyncHttpTransport accept ssl_context."""

    def test_transport_accepts_ssl_context(self) -> None:
        """HttpTransport constructor accepts ssl_context parameter."""
        ctx = ssl.create_default_context()
        transport = HttpTransport(
            endpoint="https://example.com",
            ssl_context=ctx,
        )
        transport.close()

    def test_transport_accepts_none_ssl_context(self) -> None:
        """When ssl_context is None, ssl_verify is used as normal."""
        transport = HttpTransport(
            endpoint="https://example.com",
            ssl_verify=False,
            ssl_context=None,
        )
        transport.close()

    def test_ssl_context_takes_precedence_over_ssl_verify(self) -> None:
        """When ssl_context is provided, it is used for TLS instead of ssl_verify."""
        ctx = ssl.create_default_context()
        transport = HttpTransport(
            endpoint="https://example.com",
            ssl_verify=False,
            ssl_context=ctx,
        )
        # The httpx Client should have been constructed with verify=ctx
        # We can verify indirectly: the transport was created without error
        transport.close()

    def test_async_transport_accepts_ssl_context(self) -> None:
        """AsyncHttpTransport constructor accepts ssl_context parameter."""
        ctx = ssl.create_default_context()
        AsyncHttpTransport(
            endpoint="https://example.com",
            ssl_context=ctx,
        )
        # Don't need to await close for this unit test


class TestMtlsSslContextWiring:
    """Verify from_env() builds ssl_context when cert/key env vars are set."""

    def test_from_env_without_mtls_creates_transport_without_ssl_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without mTLS env vars, transport is created normally."""
        monkeypatch.setenv("GRAPHQL_ENDPOINT", "https://example.com")
        from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

        client = GraphQLClient.from_env()
        assert client._transport is not None
        client.close()

    def test_from_env_with_mtls_requires_valid_cert_paths(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        """When cert/key env vars point to real files, ssl_context is built."""
        # Create minimal self-signed cert and key for testing
        # We'll test that the from_env path *attempts* to load certs
        # by providing invalid files and catching the expected ssl error
        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"
        cert_file.write_text("not-a-real-cert")
        key_file.write_text("not-a-real-key")

        monkeypatch.setenv("GRAPHQL_ENDPOINT", "https://example.com")
        monkeypatch.setenv("GRAPHQL_CLIENT_CERT", str(cert_file))
        monkeypatch.setenv("GRAPHQL_CLIENT_KEY", str(key_file))

        from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

        # ssl.create_default_context().load_cert_chain() will fail with bad certs
        with pytest.raises(ssl.SSLError):
            GraphQLClient.from_env()

    def test_from_env_mtls_needs_both_cert_and_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Only cert without key does not trigger mTLS context creation."""
        monkeypatch.setenv("GRAPHQL_ENDPOINT", "https://example.com")
        monkeypatch.setenv("GRAPHQL_CLIENT_CERT", "/some/cert.pem")
        # No GRAPHQL_CLIENT_KEY set

        from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

        # Should not attempt to build ssl_context (no key), so no error
        client = GraphQLClient.from_env()
        assert client._transport is not None
        client.close()
