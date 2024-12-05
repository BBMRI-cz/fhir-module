# Data model

The core domain data model follows the "Individual" level component of
the [MIABIS specification](https://github.com/BBMRI-ERIC/miabis) as close as reasonably possible.
For extending base entities, please create custom classes with appropriate inheritance.


Another model that this FHIR module supports is [MIABIS on FHIR](https://simplifier.net/miabis) profile,
currently in a separate fhir store. This implementation of the profile serves as a pilot usecase
of this new profile, with the aims of future integration of this profile to the BBMRI-ERIC Locator.
## Sample collections

The FHIR module supports the assignment of samples to Sample Collections.
This serves multiple purposes such as data quality, aggregated statistics and responsibility management.
To assign your desired collections, supply a JSON file according to
the [documentation](DEPLOYMENT.md#environment-variables).

## Useful links

- [BBMRI.de FHIR profile](https://simplifier.net/bbmri.de) (The FHIR profile/data model currently used in
  BBMRI-ERIC Locator.)
- [MIABIS on FHIR profile](https://simplifier.net/miabis) (New profile based on MIABIS Core 3.0 and individual-level components)
- [Python library for MIABIS on FHIR](https://pypi.org/project/MIABIS-on-FHIR/) (library for easier working with MIABIS on FHIR. parts of library: **miabis_model module** - classes representing the MIABIS on FHIR data model, **blaze_client** - methods for communicating with Samply Blaze store - FHIR storage server)
- [BBMRI.de FHIR Implementation guide](https://samply.github.io/bbmri-fhir-ig/)