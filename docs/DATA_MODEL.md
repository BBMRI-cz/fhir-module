# Data model

The core domain data model follows the "Individual" level component of
the [MIABIS specification](https://github.com/BBMRI-ERIC/miabis) as close as reasonably possible.
For extending base entities, please create custom classes with appropriate inheritance.

## Sample collections

The FHIR module supports the assignment of samples to Sample Collections.
This serves multiple purposes such as data quality, aggregated statistics and responsibility management.
To assign your desired collections, supply a JSON file according to
the [documentation](DEPLOYMENT.md#environment-variables).

## Useful links

- [MIABIS FHIR profile](https://simplifier.net/bbmri.de) (The FHIR profile/data model currently used in
  BBMRI-ERIC Locator.)
- [BBMRI.de FHIR Implementation guide](https://samply.github.io/bbmri-fhir-ig/)