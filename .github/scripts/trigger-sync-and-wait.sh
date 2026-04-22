#!/bin/bash -e

FHIR_MODULE_URL="${1:-http://localhost:5000}"
SYNC_ENDPOINT="$FHIR_MODULE_URL/sync"
PROGRESS_ENDPOINT="$FHIR_MODULE_URL/sync-progress"
TIMEOUT=120

echo "Waiting for fhir-module to be ready at $FHIR_MODULE_URL ..."
START="$(date +%s)"
until curl -sf "$FHIR_MODULE_URL/sync-progress" > /dev/null 2>&1; do
  if [[ $(( $(date +%s) - START )) -ge $TIMEOUT ]]; then
    echo "Timed out waiting for fhir-module" && exit 1
  fi
  sleep 2
done

echo "Triggering sync..."
curl -sf -X POST "$SYNC_ENDPOINT"
echo ""

echo "Waiting for sync to complete..."
START="$(date +%s)"
while true; do
  IN_PROGRESS=$(curl -sf "$PROGRESS_ENDPOINT" | jq -r '.in_progress')
  if [[ "$IN_PROGRESS" == "false" || "$IN_PROGRESS" == "0" ]]; then
    echo "Sync completed."
    break
  fi
  if [[ $(( $(date +%s) - START )) -ge $TIMEOUT ]]; then
    echo "Timed out waiting for sync to complete" && exit 1
  fi
  sleep 3
done