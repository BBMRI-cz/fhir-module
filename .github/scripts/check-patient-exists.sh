#!/bin/bash -e

NUM_OF_PATIENTS=$(curl -X GET http://localhost:8080/fhir/Patient?_summary=count | jq .total)
NUM_OF_CONDITIONS=$(curl -X GET http://localhost:8080/fhir/Condition?_summary=count | jq .total)
if [ "$NUM_OF_PATIENTS" = 0 ] || [ "$NUM_OF_CONDITIONS" = 0 ]; then
	echo "The upload of patients or conditions failed." && exit 1
fi