export const fhirUpQuery = `{__name__="up", instance="fhir-module:5000", job="fhir-module"}`;
export const fhirLastSyncQuery = `max(max_over_time(fhir_last_sync_timestamp{service="blaze", instance="fhir-module:5000"}[30d]) * 1000)`;
