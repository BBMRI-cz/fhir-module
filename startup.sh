#!/bin/bash
set -e

readonly SEPARATOR="=========================================="

echo "$SEPARATOR"
echo "Starting FHIR Module Container"
echo "$SEPARATOR"

mkdir -p /app/data
chown -R nextjs:nodejs /app/data

# Fix permissions for shared_config.json if it exists
if [[ -f "/opt/fhir-module/util/shared_config.json" ]]; then
    echo "Fixing permissions for shared_config.json"
    chmod 666 /opt/fhir-module/util/shared_config.json || echo "Failed to chmod shared_config.json"
fi

echo "Database will be initialized automatically when the UI starts"

echo ""
echo "$SEPARATOR"
echo "Starting supervisord to manage services..."
echo "$SEPARATOR"
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

