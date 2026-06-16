"""Tests for log correlation — otelTraceID/otelSpanID in log records (OTEL-04)."""

from __future__ import annotations

import logging

import httpx
import respx

from graphql_mcp.adapters.outbound.http_transport import HttpTransport


class RecordCapture(logging.Handler):
    """Custom handler that captures LogRecord objects for assertion."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class TestLogCorrelation:
    """Verify that LoggingInstrumentor injects trace context into log records."""

    def test_log_record_contains_trace_id_and_span_id(self, otel_setup) -> None:
        """Log records during an active span contain otelTraceID and otelSpanID."""
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        # set_logging_format=True is required for otelTraceID/otelSpanID attributes
        # to be injected onto LogRecord objects. With False, the factory is a no-op
        # unless a log_hook is also provided.
        # Uninstrument first in case a previous test (e.g. init_otel) left it instrumented.
        instrumentor = LoggingInstrumentor()
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
        instrumentor.instrument(set_logging_format=True)

        capture = RecordCapture()
        log = logging.getLogger("graphql_mcp.test.correlation")
        log.addHandler(capture)
        log.setLevel(logging.DEBUG)

        try:
            tracer = otel_setup["tracer_provider"].get_tracer("test")
            with tracer.start_as_current_span("test-op") as span:
                log.info("test message inside span")
                span_ctx = span.get_span_context()

            assert len(capture.records) >= 1, "Expected at least 1 log record"
            record = capture.records[-1]

            # LoggingInstrumentor adds otelTraceID and otelSpanID attributes
            assert hasattr(record, "otelTraceID"), f"Log record missing otelTraceID. Attrs: {record.__dict__}"
            assert hasattr(record, "otelSpanID"), f"Log record missing otelSpanID. Attrs: {record.__dict__}"

            # Verify the trace ID matches the active span
            expected_trace_id = format(span_ctx.trace_id, "032x")
            assert record.otelTraceID == expected_trace_id, (
                f"Expected trace_id={expected_trace_id}, got {record.otelTraceID}"
            )

            expected_span_id = format(span_ctx.span_id, "016x")
            assert record.otelSpanID == expected_span_id, (
                f"Expected span_id={expected_span_id}, got {record.otelSpanID}"
            )

            # Trace ID should not be zero
            assert record.otelTraceID != "0" * 32, "Trace ID should not be zero"
            assert record.otelSpanID != "0" * 16, "Span ID should not be zero"
        finally:
            log.removeHandler(capture)
            instrumentor.uninstrument()

    def test_log_record_outside_span_has_zero_ids(self, otel_setup) -> None:
        """Log records outside a span have zero trace/span IDs."""
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        instrumentor = LoggingInstrumentor()
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
        instrumentor.instrument(set_logging_format=True)

        capture = RecordCapture()
        log = logging.getLogger("graphql_mcp.test.no_span")
        log.addHandler(capture)
        log.setLevel(logging.DEBUG)

        try:
            # Log WITHOUT an active span
            log.info("test message without span")

            assert len(capture.records) >= 1
            record = capture.records[-1]

            assert hasattr(record, "otelTraceID"), "Expected otelTraceID attribute"
            # LoggingInstrumentor sets default otelTraceID to "0" (not zero-padded)
            # when no span is active. Accept either "0" or "0"*32.
            assert record.otelTraceID in ("0", "0" * 32), (
                f"Expected zero/default trace_id outside span, got {record.otelTraceID}"
            )
        finally:
            log.removeHandler(capture)
            instrumentor.uninstrument()

    @respx.mock
    def test_transport_log_has_trace_context(self, otel_setup) -> None:
        """Transport error logs carry the active span's trace context."""
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        instrumentor = LoggingInstrumentor()
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
        instrumentor.instrument(set_logging_format=True)

        capture = RecordCapture()
        transport_logger = logging.getLogger("graphql_mcp.adapters.outbound.http_transport")
        transport_logger.addHandler(capture)

        try:
            # Mock a connection error to trigger the transport's logger.warning()
            respx.post("http://log-test.example/graphql/").mock(side_effect=httpx.ConnectError("mock connection error"))

            tracer = otel_setup["tracer_provider"].get_tracer("test")
            transport = HttpTransport(endpoint="http://log-test.example/graphql")

            with tracer.start_as_current_span("test-query") as span:
                transport.execute("{ hello }")
                span_ctx = span.get_span_context()

            transport.close()

            # The transport should have logged a warning
            warning_records = [r for r in capture.records if r.levelno >= logging.WARNING]
            assert len(warning_records) >= 1, (
                f"Expected at least 1 warning log record from transport. "
                f"Got {len(capture.records)} total records: "
                f"{[r.msg for r in capture.records]}"
            )

            record = warning_records[-1]
            assert hasattr(record, "otelTraceID"), f"Transport log record missing otelTraceID. Attrs: {record.__dict__}"

            expected_trace_id = format(span_ctx.trace_id, "032x")
            assert record.otelTraceID == expected_trace_id, (
                f"Expected trace_id={expected_trace_id}, got {record.otelTraceID}"
            )
        finally:
            transport_logger.removeHandler(capture)
            instrumentor.uninstrument()
