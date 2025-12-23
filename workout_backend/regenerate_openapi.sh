#!/bin/bash
# Script to regenerate OpenAPI specification

cd "$(dirname "$0")"

# Run the OpenAPI generation script
python -m src.api.generate_openapi

echo "OpenAPI specification regenerated successfully at interfaces/openapi.json"
