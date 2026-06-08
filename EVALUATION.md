# Phase 6 — Performance Evaluation

## Codec Benchmarks

### Methodology

- **Tool**: pytest-benchmark 4.x+
- **Payloads**: 100KB (~1,200 nested objects) and 1MB (~12,000 nested objects) JSON
- **Codecs tested**: RustJsonCodec (serde_json via pyo3), OrjsonCodec (orjson fallback)
- **Operations**: encode (Python dict -> JSON bytes), decode (JSON bytes -> Python dict)
- **Invocation**: `pytest --benchmark-enable tests/benchmarks/ -v`
- **JSON output**: `pytest --benchmark-enable tests/benchmarks/ -v --benchmark-json=benchmark_results.json`

### Payload Structure

Each payload key contains a nested dict with:
- `value`: integer counter
- `nested`: dict with `z_key` (bool) and `a_key` (string) — tests sorted-key ordering
- `list`: 3-element integer list — tests array serialization

Sizes:
- **100KB**: 1,200 keys (~100KB when JSON-encoded)
- **1MB**: 12,000 keys (~1MB when JSON-encoded)

### Thresholds

| Benchmark | Threshold | Rationale |
|-----------|-----------|-----------|
| orjson encode 100KB | < 5ms median | orjson is known-fast; baseline reference |
| orjson encode 1MB | < 50ms median | Linear scaling expectation |
| orjson decode 100KB | < 5ms median | Symmetric with encode |
| orjson decode 1MB | < 50ms median | Linear scaling |
| rust vs orjson 1MB | Rust >= orjson speed | Rust codec should match or exceed orjson; if not, document as I/O-bound |

### Interpretation

- If Rust native codec is >10% faster than orjson on 1MB encode: **native codec justified**
- If Rust native codec is within +/-10% of orjson: **I/O-bound** — network latency dominates, codec choice is architectural (Rust extension for future hot paths)
- If Rust native codec is >10% slower than orjson: **investigate** — possible pyo3 marshalling overhead

### Results

_Run benchmarks to populate:_

```
pytest --benchmark-enable tests/benchmarks/ -v --benchmark-json=benchmark_results.json
```

Results will be filled in after first benchmark run.

### Transport Round-Trip

Transport round-trip benchmarks are deferred — real network latency dwarfs codec time.
Codec benchmarks are the meaningful comparison (CPU-bound, reproducible).
The sync HttpTransport and AsyncHttpTransport both use the same codec path;
transport-level benchmarking would measure httpx + network, not our code.
