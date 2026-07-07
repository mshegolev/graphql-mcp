"""Tests for OTEL bootstrap env-based configuration (OTEL-05)."""

from __future__ import annotations

import generic_graphql_mcp.adapters.outbound.otel_bootstrap as otel_bootstrap


class TestOtelBootstrap:
    """Verify init_otel reads env vars and configures providers."""

    def test_init_otel_with_endpoint(self, monkeypatch) -> None:
        """init_otel with OTEL_EXPORTER_OTLP_ENDPOINT creates real TracerProvider."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        # Reset module state so init_otel will run fresh
        monkeypatch.setattr(otel_bootstrap, "_initialized", False)
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
        monkeypatch.setenv("OTEL_SERVICE_NAME", "test-svc")

        otel_bootstrap.init_otel()

        provider = trace.get_tracer_provider()
        # May be wrapped in a ProxyTracerProvider; unwrap
        actual = getattr(provider, "_real_provider", provider)
        assert isinstance(actual, TracerProvider), f"Expected TracerProvider, got {type(actual)}"

        # Clean up: shutdown the provider we just created
        if isinstance(actual, TracerProvider):
            actual.shutdown()
        monkeypatch.setattr(otel_bootstrap, "_initialized", False)

    def test_init_otel_without_packages(self, monkeypatch) -> None:
        """init_otel is no-op when _OTEL_AVAILABLE is False."""
        monkeypatch.setattr(otel_bootstrap, "_OTEL_AVAILABLE", False)
        monkeypatch.setattr(otel_bootstrap, "_initialized", False)

        # Should return without error
        otel_bootstrap.init_otel()

        # Restore
        monkeypatch.setattr(otel_bootstrap, "_OTEL_AVAILABLE", True)

    def test_init_otel_idempotent(self, monkeypatch) -> None:
        """Calling init_otel twice does not error."""
        monkeypatch.setattr(otel_bootstrap, "_initialized", False)
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

        otel_bootstrap.init_otel()
        otel_bootstrap.init_otel()  # second call — must be safe

        # Reset for other tests
        monkeypatch.setattr(otel_bootstrap, "_initialized", False)

    def test_is_otel_available_returns_true(self) -> None:
        """is_otel_available() returns True when packages are installed."""
        assert otel_bootstrap.is_otel_available() is True

    def test_get_tracer_returns_tracer(self) -> None:
        """get_tracer() returns a Tracer object (not None)."""
        tracer = otel_bootstrap.get_tracer("test")
        assert tracer is not None

    def test_get_meter_returns_meter(self) -> None:
        """get_meter() returns a Meter object (not None)."""
        meter = otel_bootstrap.get_meter("test")
        assert meter is not None
