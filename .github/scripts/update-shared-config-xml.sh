#!/bin/bash -e

# Update shared_config.json with values for XML test configuration
CONFIG_FILE=${1:-"util/shared_config.json"}

echo "Updating $CONFIG_FILE for XML test configuration..."

# Update RECORDS_DIR_PATH for XML tests (other values are already correct in defaults)
jq '.RECORDS_DIR_PATH = "/opt/records"' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"

echo "Updated configuration:"
echo "  - RECORDS_DIR_PATH: /opt/records"
echo "Configuration updated successfully!"

