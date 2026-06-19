#!/usr/bin/env python3
"""
Validate the OpenAPI specification files.
"""

import json
import yaml
from pathlib import Path


def validate_openapi_yaml():
    """Validate the OpenAPI YAML file."""
    yaml_path = Path("openapi.yaml")
    if not yaml_path.exists():
        print("❌ openapi.yaml not found")
        return False

    try:
        with open(yaml_path, "r") as f:
            spec = yaml.safe_load(f)

        # Basic validation
        assert "openapi" in spec, "Missing 'openapi' field"
        assert "info" in spec, "Missing 'info' field"
        assert "title" in spec["info"], "Missing 'title' in info"
        assert "version" in spec["info"], "Missing 'version' in info"
        assert "paths" in spec, "Missing 'paths' field"

        print("✅ openapi.yaml is valid")
        return True
    except Exception as e:
        print(f"❌ openapi.yaml validation failed: {e}")
        return False


def validate_openapi_json():
    """Validate the OpenAPI JSON file."""
    json_path = Path("openapi.json")
    if not json_path.exists():
        print("❌ openapi.json not found")
        return False

    try:
        with open(json_path, "r") as f:
            spec = json.load(f)

        # Basic validation
        assert "openapi" in spec, "Missing 'openapi' field"
        assert "info" in spec, "Missing 'info' field"
        assert "title" in spec["info"], "Missing 'title' in info"
        assert "version" in spec["info"], "Missing 'version' in info"
        assert "paths" in spec, "Missing 'paths' field"

        print("✅ openapi.json is valid")
        return True
    except Exception as e:
        print(f"❌ openapi.json validation failed: {e}")
        return False


def main():
    """Main validation function."""
    print("Validating OpenAPI specification files...")

    yaml_valid = validate_openapi_yaml()
    json_valid = validate_openapi_json()

    if yaml_valid and json_valid:
        print("\n✅ All OpenAPI specification files are valid!")
        return True
    else:
        print("\n❌ Some OpenAPI specification files are invalid!")
        return False


if __name__ == "__main__":
    exit(0 if main() else 1)
