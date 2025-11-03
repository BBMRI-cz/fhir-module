#!/bin/bash -e

# Check if a URL was provided as an argument
if [[ -z "$1" ]]; then
    echo "Usage: $0 <base-url>"
    echo "Example: $0 http://localhost:8080/fhir"
    exit 1
fi

# Get the base URL from the first argument
BASE_URL="$1"

NUM_OF_PATIENTS=$(curl -s -X GET ${BASE_URL}/Patient?_summary=count | jq .total)
NUM_OF_CONDITIONS=$(curl -s -X GET ${BASE_URL}/Condition?_summary=count | jq .total)
NUM_OF_SPECIMENS=$(curl -s -X GET ${BASE_URL}/Specimen?_summary=count | jq .total)

echo "Number of Patients: $NUM_OF_PATIENTS"
echo "Number of Conditions: $NUM_OF_CONDITIONS"
echo "Number of Specimens: $NUM_OF_SPECIMENS"

if [[ "$NUM_OF_PATIENTS" -eq 0 ]] || [[ "$NUM_OF_CONDITIONS" -eq 0 ]] || [[ "$NUM_OF_SPECIMENS" -eq 0 ]]; then
	echo "The upload of resources failed." && exit 1
fi

echo "All resources uploaded successfully!"