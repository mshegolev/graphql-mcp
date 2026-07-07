# ---- Build stage ----
# Rust toolchain + Python for maturin/pyo3 native extension build
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential pkg-config && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /build

# Copy build manifests first (cache-friendly layer ordering)
COPY pyproject.toml Cargo.toml ./
COPY native/ native/

# Copy Python source
COPY src/ src/

# Build wheel with maturin (compiles Rust extension + packages Python)
RUN pip install --no-cache-dir "maturin>=1.0,<2.0" && \
    maturin build --release --strip -o dist/

# ---- Runtime stage ----
# Minimal image — no Rust toolchain, no build artifacts
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

WORKDIR /app

# Install the built wheel then add optional extras for server+mcp+cli
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && \
    pip install --no-cache-dir \
        'fastapi>=0.100,<1' \
        'uvicorn>=0.20,<1' \
        'mcp>=1.0,<2' \
        'click>=8,<9' && \
    rm -rf /tmp/*.whl

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check using /health endpoint (stdlib only — no curl needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["generic-graphql-mcp", "serve"]
