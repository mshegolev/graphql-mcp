# Makefile for OpenAPI specification tasks

.PHONY: validate convert-yaml-to-json convert-json-to-yaml help

help:
	@echo "OpenAPI Specification Tasks"
	@echo "=========================="
	@echo "validate            - Validate OpenAPI specification files"
	@echo "convert-yaml-to-json - Convert YAML to JSON format"
	@echo "convert-json-to-yaml - Convert JSON to YAML format"
	@echo "help                - Show this help message"

validate:
	@echo "Validating OpenAPI specification files..."
	@python3 ./validate.py

convert-yaml-to-json:
	@echo "Converting YAML to JSON..."
	@python3 ./convert.py openapi.yaml openapi.json

convert-json-to-yaml:
	@echo "Converting JSON to YAML..."
	@python3 ./convert.py openapi.json openapi.yaml

clean:
	@echo "Cleaning up..."
	@rm -f *.tmp