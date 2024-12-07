#!/bin/bash -e

# Check if a URL was provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <base-url>"
    echo "Example: $0 http://localhost:8080/fhir"
    exit 1
fi

# Get the base URL from the first argument
BASE_URL="$1"

NUM_OF_PATIENTS=$(curl -X GET ${BASE_URL}/Patient?_summary=count | jq .total)
NUM_OF_CONDITIONS=$(curl -X GET ${BASE_URL}/fhir/Condition?_summary=count | jq .total)
NUM_OF_SPECIMENS=$(curl -X GET ${BASE_URL}/fhir/Specimen?_summary=count | jq .total)
if [ "$NUM_OF_PATIENTS" = 0 ] || [ "$NUM_OF_CONDITIONS" = 0 ] || [ "$NUM_OF_SPECIMENS" = 0 ]; then
	echo "The upload of resources failed." && exit 1
fi