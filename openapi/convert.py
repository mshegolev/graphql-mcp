#!/usr/bin/env python3
"""
Utility script to convert between OpenAPI YAML and JSON formats.
"""

import json
import yaml
import argparse
from pathlib import Path


def yaml_to_json(yaml_path, json_path):
    """Convert YAML to JSON."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Converted {yaml_path} to {json_path}")


def json_to_yaml(json_path, yaml_path):
    """Convert JSON to YAML."""
    with open(json_path, "r") as f:
        data = json.load(f)

    with open(yaml_path, "w") as f:
        yaml.dump(data, f, indent=2, allow_unicode=True, sort_keys=False)

    print(f"Converted {json_path} to {yaml_path}")


def main():
    """Main conversion function."""
    parser = argparse.ArgumentParser(description="Convert between OpenAPI YAML and JSON formats")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return 1

    if input_path.suffix.lower() == ".yaml" or input_path.suffix.lower() == ".yml":
        if output_path.suffix.lower() == ".json":
            yaml_to_json(input_path, output_path)
        else:
            print("Error: Output file must have .json extension when converting from YAML")
            return 1
    elif input_path.suffix.lower() == ".json":
        if output_path.suffix.lower() == ".yaml" or output_path.suffix.lower() == ".yml":
            json_to_yaml(input_path, output_path)
        else:
            print("Error: Output file must have .yaml or .yml extension when converting from JSON")
            return 1
    else:
        print("Error: Input file must have .yaml, .yml, or .json extension")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
