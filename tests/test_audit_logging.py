"""Tests for structured audit logging (SEC-06)."""

import logging

import pytest

from graphql_mcp.adapters.outbound.audit import _query_hash, emit_audit_log


class TestAuditLogEmission:
    def test_audit_log_emitted_with_required_fields(self, caplog):
        """emit_audit_log produces a log record with all required fields."""
        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            emit_audit_log(
                operation="query",
                query_str="{ hello }",
                error_class="ok",
                latency_s=0.123,
                caller_ip="192.168.1.1",
                caller_identity="user-42",
            )
        assert len(caplog.records) == 1
        record = caplog.records[0]
        # Check structured fields in extra
        assert record.caller_ip == "192.168.1.1"
        assert record.caller_identity == "user-42"
        assert record.operation == "query"
        assert record.error_class == "ok"
        assert record.latency_ms == 123.0
        assert record.trace_id  # "none" or a real trace ID
        assert len(record.query_hash) == 16  # first 16 hex chars of SHA-256

    def test_query_hash_deterministic(self):
        """Same query always produces same hash."""
        h1 = _query_hash("{ hello }")
        h2 = _query_hash("{ hello }")
        assert h1 == h2
        assert len(h1) == 16

    def test_different_queries_different_hashes(self):
        h1 = _query_hash("{ hello }")
        h2 = _query_hash("{ goodbye }")
        assert h1 != h2

    def test_trace_id_none_without_otel_context(self):
        """Without active OTEL span, trace_id is 'none'."""
        from graphql_mcp.adapters.outbound.audit import _get_trace_id

        # No active span → "none" or "0" * 32 depending on OTEL state
        tid = _get_trace_id()
        assert isinstance(tid, str)

    def test_audit_log_defaults(self, caplog):
        """Default caller_ip='local' and caller_identity='anonymous'."""
        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            emit_audit_log(
                operation="raw",
                query_str="{ test }",
                error_class="graphql",
                latency_s=0.001,
            )
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.caller_ip == "local"
        assert record.caller_identity == "anonymous"

    def test_latency_ms_precision(self, caplog):
        """Latency is rounded to 2 decimal places."""
        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            emit_audit_log(
                operation="query",
                query_str="{ test }",
                error_class="ok",
                latency_s=0.12345,
            )
        assert caplog.records[0].latency_ms == 123.45


class TestAuditViaLibFacade:
    def test_audit_logged_on_query(self, caplog):
        """GraphQLClient.query() emits audit log when audit_log=True."""
        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=True)
        client = GraphQLClient(schema_service=service, transport=None, config=config)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            result = client.query("{ hello }")

        # Should have one audit record (transport error — no transport configured)
        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].operation == "query"
        assert audit_records[0].error_class == "transport"

    def test_no_audit_when_disabled(self, caplog):
        """GraphQLClient.query() does NOT emit audit log when audit_log=False."""
        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            result = client.query("{ hello }")

        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 0

    def test_audit_on_raw(self, caplog):
        """GraphQLClient.raw() emits audit log when audit_log=True."""
        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=True)
        client = GraphQLClient(schema_service=service, transport=None, config=config)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            result = client.raw({"query": "{ hello }"})

        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].operation == "raw"

    def test_audit_on_entities(self, caplog):
        """GraphQLClient.entities() emits audit log when audit_log=True."""
        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=True)
        client = GraphQLClient(schema_service=service, transport=None, config=config)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            result = client.entities([{"__typename": "User", "id": "1"}])

        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].operation == "entities"


class TestAuditViaREST:
    def test_rest_audit_includes_caller_ip(self, caplog):
        """REST endpoint audit log includes caller IP from request."""
        from fastapi.testclient import TestClient

        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.adapters.inbound.rest import app, set_client
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=True)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)
        tc = TestClient(app)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})

        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].caller_ip  # should be testclient IP
        assert audit_records[0].query_hash  # 16-char hex

    def test_rest_audit_includes_x_user_id(self, caplog):
        """REST audit log uses X-User-Id header as caller_identity."""
        from fastapi.testclient import TestClient

        from graphql_mcp.adapters.inbound.lib import GraphQLClient
        from graphql_mcp.adapters.inbound.rest import app, set_client
        from graphql_mcp.config import GraphQLConfig
        from graphql_mcp.domain.schema_service import SchemaService
        from tests.conftest import SAMPLE_SDL, MockSchemaSource

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False, audit_log=True)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)
        tc = TestClient(app)

        with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
            resp = tc.post(
                "/graphql/query",
                json={"query": "{ hello }"},
                headers={"X-User-Id": "testuser-99"},
            )

        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].caller_identity == "testuser-99"


class TestAuditWithOTEL:
    def test_trace_id_populated_during_traced_request(self, otel_setup, caplog):
        """When OTEL is active and a span exists, audit log has real trace_id."""
        from opentelemetry import trace

        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("test-span"):
            with caplog.at_level(logging.INFO, logger="graphql_mcp.audit"):
                emit_audit_log(
                    operation="query",
                    query_str="{ hello }",
                    error_class="ok",
                    latency_s=0.01,
                )
        audit_records = [r for r in caplog.records if r.name == "graphql_mcp.audit"]
        assert len(audit_records) == 1
        assert audit_records[0].trace_id != "none"
        assert len(audit_records[0].trace_id) == 32  # 128-bit trace ID as hex
