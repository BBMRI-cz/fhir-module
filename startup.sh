#!/bin/bash
set -e

echo "=========================================="
echo "Starting FHIR Module Container"
echo "=========================================="

mkdir -p /app/data
chown -R nextjs:nodejs /app/data

echo "Database will be initialized automatically when the UI starts"

echo ""
echo "=========================================="
echo "Starting supervisord to manage services..."
echo "=========================================="
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

