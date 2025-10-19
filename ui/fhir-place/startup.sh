#!/bin/bash
set -e

echo "Running database migrations..."
npm run db:migrate

echo "Initializing database..."
npm run db:init

echo "Starting Next.js server..."
exec node server.js

