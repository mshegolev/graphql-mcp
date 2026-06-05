from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DOMAIN_DIR = Path(__file__).resolve().parent.parent / "src" / "graphql_mcp" / "domain"
PORTS_DIR = Path(__file__).resolve().parent.parent / "src" / "graphql_mcp" / "ports"

FORBIDDEN_IMPORTS = [
    "import httpx",
    "import requests",
    "import fastapi",
    "import pathlib",
    "from httpx",
    "from requests",
    "from fastapi",
    "from pathlib",
]


def _scan_directory(directory: Path) -> list[str]:
    """Scan all .py files in directory for forbidden imports."""
    violations: list[str] = []
    for py_file in directory.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue
            for forbidden in FORBIDDEN_IMPORTS:
                if forbidden in stripped:
                    violations.append(f"{py_file.name}:{line_no}: {stripped}")
    return violations


def test_domain_has_no_io_imports():
    """domain/ must not import any I/O or framework libraries."""
    violations = _scan_directory(DOMAIN_DIR)
    assert violations == [], "I/O imports found in domain/:\n" + "\n".join(violations)


def test_ports_have_no_io_imports():
    """ports/ must not import any I/O or framework libraries."""
    violations = _scan_directory(PORTS_DIR)
    assert violations == [], "I/O imports found in ports/:\n" + "\n".join(violations)


def test_domain_purity_via_grep():
    """Belt-and-suspenders: grep for forbidden imports."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import subprocess, sys; "
            "r = subprocess.run("
            "['grep', '-rn', '-E', "
            "'import (httpx|requests|fastapi|pathlib)|from (httpx|requests|fastapi|pathlib)', "
            f"'{DOMAIN_DIR}', '{PORTS_DIR}'], "
            "capture_output=True, text=True); "
            "print(r.stdout); sys.exit(r.returncode)",
        ],
        capture_output=True,
        text=True,
    )
    # grep returns 1 when no matches found (which is what we want)
    assert result.stdout.strip() == "" or result.returncode == 1, f"Forbidden imports found:\n{result.stdout}"
