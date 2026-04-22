#!/bin/bash -e

FHIR_MODULE_URL="${1:-http://localhost:5000}"
TIMEOUT=120

echo "Waiting for fhir-module to be ready at $FHIR_MODULE_URL ..."
START="$(date +%s)"
until curl -sf "$FHIR_MODULE_URL/sync-progress" > /dev/null 2>&1; do
  if [[ $(( $(date +%s) - START )) -ge $TIMEOUT ]]; then
    echo "Timed out waiting for fhir-module" && exit 1
  fi
  sleep 2
done

wait_for_sync() {
  local PROGRESS_ENDPOINT="$1"
  local LABEL="$2"
  echo "Waiting for $LABEL sync to complete..."
  START="$(date +%s)"
  while true; do
    IN_PROGRESS=$(curl -sf "$PROGRESS_ENDPOINT" | jq -r '.in_progress')
    if [[ "$IN_PROGRESS" == "false" || "$IN_PROGRESS" == "0" ]]; then
      echo "$LABEL sync completed."
      break
    fi
    if [[ $(( $(date +%s) - START )) -ge $TIMEOUT ]]; then
      echo "Timed out waiting for $LABEL sync to complete" && exit 1
    fi
    sleep 3
  done
}

echo "Triggering standard sync..."
curl -sf -X POST "$FHIR_MODULE_URL/sync"
echo ""
wait_for_sync "$FHIR_MODULE_URL/sync-progress" "standard"

echo "Triggering MIABIS sync..."
MIABIS_RESPONSE=$(curl -sf -X POST "$FHIR_MODULE_URL/miabis-sync" 2>&1)
echo "$MIABIS_RESPONSE"
if echo "$MIABIS_RESPONSE" | grep -q "error"; then
  echo "MIABIS sync not available, skipping."
else
  wait_for_sync "$FHIR_MODULE_URL/miabis-sync-progress" "MIABIS"
fi