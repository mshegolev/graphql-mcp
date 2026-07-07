"""Tests for the Copier template — generates a brick and validates it."""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent.parent / "template"
HARDCODED_PATTERNS = [
    "generic_graphql_mcp",
    "generic-graphql-mcp",
    "GRAPHQL_",
    "GraphqlMcp",
]

# Allowlisted files that may legitimately reference the parent project
ALLOWLISTED_FILES = {".copier-answers.yml"}


@pytest.fixture(scope="module")
def generated_project(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Generate a project from the Copier template with test defaults."""
    dst = tmp_path_factory.mktemp("generated_brick")

    from copier import run_copy

    run_copy(
        src_path=str(TEMPLATE_DIR),
        dst_path=str(dst),
        data={
            "module_name": "kafka_mcp",
            "package_name": "kafka-mcp",
            "description": "Kafka investigation MCP brick",
            "env_prefix": "KAFKA",
            "python_version": "3.10",
            "rust_native": False,
            "subscriptions": False,
            "otel": False,
        },
        defaults=True,
        unsafe=True,
    )
    return dst


class TestGeneratedStructure:
    """Verify the generated project has the expected file structure."""

    def test_pyproject_toml_exists(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "pyproject.toml").is_file()

    def test_dockerfile_exists(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "Dockerfile").is_file()

    def test_module_init_exists(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "__init__.py").is_file()

    def test_domain_models_exist(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "domain" / "models.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "domain" / "errors.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "domain" / "schema_service.py").is_file()

    def test_ports_exist(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "ports" / "transport.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "ports" / "schema_source.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "ports" / "json_codec.py").is_file()

    def test_adapters_exist(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "adapters" / "inbound" / "lib.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "adapters" / "inbound" / "cli.py").is_file()
        assert (generated_project / "src" / "kafka_mcp" / "adapters" / "outbound" / "http_transport.py").is_file()

    def test_config_exists(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "config.py").is_file()

    def test_tests_exist(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "tests" / "conftest.py").is_file()
        assert (generated_project / "tests" / "test_models.py").is_file()
        assert (generated_project / "tests" / "test_domain_purity.py").is_file()
        assert (generated_project / "tests" / "test_schema_service.py").is_file()

    def test_py_typed_marker(self, generated_project: pathlib.Path) -> None:
        assert (generated_project / "src" / "kafka_mcp" / "py.typed").is_file()


class TestNoHardcodedStrings:
    """Verify no hardcoded generic_graphql_mcp / generic-graphql-mcp / GRAPHQL_ strings remain."""

    def test_no_hardcoded_strings_in_generated_output(self, generated_project: pathlib.Path) -> None:
        """Grep all generated files for hardcoded parent-project references."""
        violations: list[str] = []

        for path in generated_project.rglob("*"):
            if not path.is_file():
                continue
            if path.name in ALLOWLISTED_FILES:
                continue
            # Skip binary files
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            rel = path.relative_to(generated_project)
            for pattern in HARDCODED_PATTERNS:
                if pattern in content:
                    violations.append(f"{rel}: contains '{pattern}'")

        assert not violations, "Hardcoded strings found in generated project:\n" + "\n".join(
            f"  - {v}" for v in violations
        )


class TestParameterization:
    """Verify Jinja2 substitution produces correct values."""

    def test_pyproject_uses_package_name(self, generated_project: pathlib.Path) -> None:
        content = (generated_project / "pyproject.toml").read_text()
        assert 'name = "kafka-mcp"' in content

    def test_config_uses_env_prefix(self, generated_project: pathlib.Path) -> None:
        content = (generated_project / "src" / "kafka_mcp" / "config.py").read_text()
        assert 'env_prefix="KAFKA_"' in content
        assert "class KafkaConfig" in content

    def test_dockerfile_uses_package_name(self, generated_project: pathlib.Path) -> None:
        content = (generated_project / "Dockerfile").read_text()
        assert 'CMD ["kafka-mcp", "serve"]' in content

    def test_init_uses_module_name(self, generated_project: pathlib.Path) -> None:
        content = (generated_project / "src" / "kafka_mcp" / "__init__.py").read_text()
        assert "from kafka_mcp.adapters.inbound.lib import GraphQLClient" in content


class TestGeneratedTestSuite:
    """Verify the generated project's own test suite passes."""

    def test_generated_tests_pass(self, generated_project: pathlib.Path) -> None:
        """Install the generated project and run its tests."""
        # Install the generated project in editable mode
        install_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            capture_output=True,
            text=True,
            cwd=str(generated_project),
            timeout=120,
        )
        assert install_result.returncode == 0, f"pip install failed:\n{install_result.stderr}"

        # Run the generated project's tests
        test_result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-x", "-v"],
            capture_output=True,
            text=True,
            cwd=str(generated_project),
            timeout=60,
        )
        assert test_result.returncode == 0, (
            f"Generated project tests failed:\n{test_result.stdout}\n{test_result.stderr}"
        )


class TestOptionalFeatures:
    """Verify optional feature flags change the generated output."""

    @pytest.fixture(scope="class")
    def full_features_project(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        """Generate a project with all optional features enabled."""
        dst = tmp_path_factory.mktemp("full_features")

        from copier import run_copy

        run_copy(
            src_path=str(TEMPLATE_DIR),
            dst_path=str(dst),
            data={
                "module_name": "ordering_mcp",
                "package_name": "ordering-mcp",
                "description": "Ordering investigation MCP brick",
                "env_prefix": "ORDERING",
                "python_version": "3.12",
                "rust_native": True,
                "subscriptions": True,
                "otel": True,
            },
            defaults=True,
            unsafe=True,
        )
        return dst

    def test_rust_native_enables_maturin(self, full_features_project: pathlib.Path) -> None:
        content = (full_features_project / "pyproject.toml").read_text()
        assert "maturin" in content
        assert "[tool.maturin]" in content

    def test_otel_adds_otel_extra(self, full_features_project: pathlib.Path) -> None:
        content = (full_features_project / "pyproject.toml").read_text()
        assert "otel" in content
        assert "opentelemetry-api" in content

    def test_subscriptions_adds_websockets_extra(self, full_features_project: pathlib.Path) -> None:
        content = (full_features_project / "pyproject.toml").read_text()
        assert "subscriptions" in content
        assert "websockets" in content

    def test_rust_native_dockerfile_has_cargo(self, full_features_project: pathlib.Path) -> None:
        content = (full_features_project / "Dockerfile").read_text()
        assert "rustup" in content
        assert "maturin build" in content

    def test_no_hardcoded_strings_full_features(self, full_features_project: pathlib.Path) -> None:
        """Even with all features enabled, no hardcoded strings."""
        violations: list[str] = []
        for path in full_features_project.rglob("*"):
            if not path.is_file():
                continue
            if path.name in ALLOWLISTED_FILES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rel = path.relative_to(full_features_project)
            for pattern in HARDCODED_PATTERNS:
                if pattern in content:
                    violations.append(f"{rel}: contains '{pattern}'")
        assert not violations, "Hardcoded strings found:\n" + "\n".join(f"  - {v}" for v in violations)
