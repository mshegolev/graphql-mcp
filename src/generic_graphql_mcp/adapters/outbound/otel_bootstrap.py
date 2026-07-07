"""OpenTelemetry bootstrap — TracerProvider + MeterProvider from env vars.

Graceful no-op when opentelemetry packages are not installed.
Call ``init_otel()`` once at application startup; all subsequent calls
are idempotent.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

try:
    from opentelemetry import metrics, trace  # noqa: F401  — import IS the availability probe

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OTEL_AVAILABLE = False

_initialized = False


def is_otel_available() -> bool:
    """Return True when the opentelemetry SDK packages are importable."""
    return _OTEL_AVAILABLE


def init_otel() -> None:
    """Initialize TracerProvider + MeterProvider from standard OTEL_* env vars.

    * ``OTEL_SERVICE_NAME``  – resource service.name (default ``generic-graphql-mcp``)
    * ``OTEL_EXPORTER_OTLP_ENDPOINT`` – if set, OTLP/HTTP exporters are added

    Safe to call multiple times — only the first invocation takes effect.
    When opentelemetry is not installed the function returns immediately.
    """
    global _initialized  # noqa: PLW0603
    if _initialized or not _OTEL_AVAILABLE:
        return
    _initialized = True

    from opentelemetry import metrics, trace
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    service_name = os.environ.get("OTEL_SERVICE_NAME", "generic-graphql-mcp")
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    resource = Resource.create({"service.name": service_name})

    # --- Tracer ---
    tracer_provider = TracerProvider(resource=resource)
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    # --- Meter ---
    metric_readers: list = []
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

        metric_readers.append(PeriodicExportingMetricReader(OTLPMetricExporter()))
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)

    # --- Auto-instrumentation ---
    HTTPXClientInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)

    logger.info("OpenTelemetry initialized (service=%s, otlp=%s)", service_name, otlp_endpoint or "none")


def get_tracer(name: str):  # noqa: ANN201
    """Return an OpenTelemetry Tracer (NoOpTracer when SDK absent)."""
    if not _OTEL_AVAILABLE:
        # Return a minimal no-op object when OTEL is unavailable

        class _NoOpSpan:
            def set_attribute(self, key, value):  # noqa: ANN001, ANN201, ARG002
                pass

            def set_status(self, status):  # noqa: ANN001, ANN201, ARG002
                pass

            def __enter__(self):  # noqa: ANN204
                return self

            def __exit__(self, *args):  # noqa: ANN002, ANN204
                pass

        class _NoOpTracer:
            def start_as_current_span(self, name, **kwargs):  # noqa: ANN001, ANN003, ANN201, ARG002
                return _NoOpSpan()

        return _NoOpTracer()
    from opentelemetry import trace

    return trace.get_tracer(name)


def get_meter(name: str):  # noqa: ANN201
    """Return an OpenTelemetry Meter (NoOpMeter when SDK absent)."""
    if not _OTEL_AVAILABLE:

        class _NoOpInstrument:
            def add(self, amount, attributes=None):  # noqa: ANN001, ANN201, ARG002
                pass

            def record(self, amount, attributes=None):  # noqa: ANN001, ANN201, ARG002
                pass

        class _NoOpMeter:
            def create_counter(self, name, **kwargs):  # noqa: ANN001, ANN003, ANN201, ARG002
                return _NoOpInstrument()

            def create_histogram(self, name, **kwargs):  # noqa: ANN001, ANN003, ANN201, ARG002
                return _NoOpInstrument()

            def create_up_down_counter(self, name, **kwargs):  # noqa: ANN001, ANN003, ANN201, ARG002
                return _NoOpInstrument()

        return _NoOpMeter()
    from opentelemetry import metrics

    return metrics.get_meter(name)
