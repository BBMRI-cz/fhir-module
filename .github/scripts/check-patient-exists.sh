#!/bin/bash -e

NUM_OF_PATIENTS=$(curl -X GET http://localhost:8080/fhir/Patient?_summary=count | jq .total)
if [ "$NUM_OF_PATIENTS" = 0 ]; then
	exit 1
fi