#!/bin/bash -e

NUM_OF_PATIENTS=$(curl -X GET http://localhost:8080/fhir/Patient?_summary=count | jq .total)
NUM_OF_CONDITIONS=$(curl -X GET http://localhost:8080/fhir/Condition?_summary=count | jq .total)
NUM_OF_SPECIMENS=$(curl -X GET http://localhost:8080/fhir/Specimen?_summary=count | jq .total)
if [ "$NUM_OF_PATIENTS" = 0 ] || [ "$NUM_OF_CONDITIONS" = 0 ] || [ "$NUM_OF_SPECIMENS" = 0 ]; then
	echo "The upload of resources failed." && exit 1
fi