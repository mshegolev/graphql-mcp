from __future__ import annotations

import pytest

from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.config import GraphQLConfig
from generic_graphql_mcp.domain.models import SchemaGraph
from generic_graphql_mcp.domain.schema_service import SchemaService

# OTEL test infrastructure
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

SAMPLE_SDL = """\
type Query {
  hello: String
  users: [User]
}

type User {
  id: ID!
  name: String!
  email: String
}
"""


class MockSchemaSource:
    """A configurable mock schema source for testing."""

    def __init__(
        self,
        source_name: str,
        sdl: str | None = None,
        should_raise: bool = False,
    ) -> None:
        self._name = source_name
        self._sdl = sdl
        self._should_raise = should_raise
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def fetch_schema(self) -> SchemaGraph | None:
        self.call_count += 1
        if self._should_raise:
            raise ConnectionError(f"Mock error from {self._name}")
        if self._sdl is None:
            return None
        return SchemaGraph(sdl=self._sdl, source_name=self._name)


SAMPLE_SUPERGRAPH_SDL = (
    "directive @join__graph(name: String!, url: String!) on ENUM_VALUE\n"
    "directive @join__type(graph: join__Graph!)"
    " on OBJECT | INTERFACE | UNION | ENUM | INPUT_OBJECT | SCALAR\n"
    "\n"
    "enum join__Graph {\n"
    '  USERS @join__graph(name: "users", url: "http://users:4001/graphql")\n'
    '  PRODUCTS @join__graph(name: "products",'
    ' url: "http://products:4002/graphql")\n'
    "}\n"
    "\n"
    "type Query {\n"
    "  users: [User]\n"
    "  products: [Product]\n"
    "}\n"
    "\n"
    "type User @join__type(graph: USERS) {\n"
    "  id: ID!\n"
    "  name: String!\n"
    "  email: String\n"
    "}\n"
    "\n"
    "type Product @join__type(graph: PRODUCTS) {\n"
    "  id: ID!\n"
    "  title: String!\n"
    "  price: Float\n"
    "}\n"
)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the rate limiter state before each test to prevent cross-test interference."""
    from generic_graphql_mcp.adapters.inbound.rest import RateLimitMiddleware, app

    middleware_stack = getattr(app, "middleware_stack", None)
    if middleware_stack is None:
        yield
        return

    current = middleware_stack
    while current is not None:
        if isinstance(current, RateLimitMiddleware):
            current._windows.clear()
            break
        current = getattr(current, "app", None)
    yield


@pytest.fixture
def sample_sdl() -> str:
    return SAMPLE_SDL


@pytest.fixture
def successful_source(sample_sdl: str) -> MockSchemaSource:
    return MockSchemaSource("test_source", sdl=sample_sdl)


@pytest.fixture
def failing_source() -> MockSchemaSource:
    return MockSchemaSource("failing_source", should_raise=True)


@pytest.fixture
def none_source() -> MockSchemaSource:
    return MockSchemaSource("none_source", sdl=None)


@pytest.fixture
def simple_client(sample_sdl: str) -> GraphQLClient:
    """GraphQLClient with mock schema source and no transport (schema-only ops)."""
    source = MockSchemaSource("test", sdl=sample_sdl)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=None, config=config)


@pytest.fixture
def otel_setup():
    """Set up in-memory OTEL exporters for testing.

    Yields a dict with ``span_exporter``, ``metric_reader``,
    ``tracer_provider``, and ``meter_provider`` for assertions.
    Tears down instrumentation after each test.
    """
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    # Reset global providers so each test gets a fresh state.
    # The OTEL API caches the first set_*_provider call and warns on
    # subsequent overrides — resetting the internal proxy forces a clean slate.
    _reset_trace_provider()
    _reset_meter_provider()

    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    HTTPXClientInstrumentor().instrument()

    yield {
        "span_exporter": span_exporter,
        "metric_reader": metric_reader,
        "tracer_provider": tracer_provider,
        "meter_provider": meter_provider,
    }

    HTTPXClientInstrumentor().uninstrument()
    tracer_provider.shutdown()
    meter_provider.shutdown()
    _reset_trace_provider()
    _reset_meter_provider()


def _reset_trace_provider() -> None:
    """Reset the global TracerProvider so tests can set a fresh one."""
    import opentelemetry.trace as _trace_mod

    # Reset the Once guard and the global provider reference
    _trace_mod._TRACER_PROVIDER_SET_ONCE = _trace_mod.Once()
    _trace_mod._TRACER_PROVIDER = None


def _reset_meter_provider() -> None:
    """Reset the global MeterProvider so tests can set a fresh one."""
    import opentelemetry.metrics._internal as _metrics_mod

    _metrics_mod._METER_PROVIDER_SET_ONCE = _metrics_mod.Once()
    _metrics_mod._METER_PROVIDER = None
