# FHIR module

[![CI build](https://github.com/BBMRI-cz/fhir-module/actions/workflows/build.yml/badge.svg)](https://github.com/BBMRI-cz/Data-Integration-Module/actions/workflows/build.yml) [![codecov](https://codecov.io/gh/BBMRI-cz/fhir-module/branch/main/graph/badge.svg?token=3eklJNhIS5)](https://codecov.io/gh/BBMRI-cz/fhir-module) [![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-360/) [![Linter: pylint](https://img.shields.io/badge/Linter-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)

The [BBMRI-ERIC](https://www.bbmri-eric.eu/) FHIR module is a container based application connecting biobanks
to other IT tools and services in our ecosystem on a local level.
## Goal

The goal of this project is to create a highly customizable data integration tool for biobanks that are a
part of BBMRI-ERIC. This tool should support ETL processes by providing the following functionality:

- Data harmonization to [HL7 FHIR](https://www.hl7.org/fhir/) (under development)
- Data quality validation (coming soon)
- Reporting and monitoring (coming soon)

## State

Supports syncing of patients between a [Blaze FHIR store](https://github.com/samply/blaze) and a repository of XML or CSV files
stored on a regular filesystem.
Currently, the XML files must have the same structure as this [test file](./test/xml_data/MMCI_1.xml).
This module cannot work with different types of files at the same time, so the records needs to be in either XML or CSV format, not both.

## Quick Start

### Docker

Prerequisites:

- [Docker engine v24.0.0](https://docs.docker.com/engine/release-notes/24.0/#2400)
- [Docker compose v2.20](https://docs.docker.com/compose/release-notes/#2200)

To spin up an instance of the FHIR module along with [Blaze](https://github.com/samply/blaze), clone the repository and
run the following command:

```shell
docker compose --profile dev up -d
```
For additional information about deployment, refer to the [Deployment documentation](docs/DEPLOYMENT.md).
## Contributing

Because the FHIR module is an open source software pull requests are of course welcome! For further information, please
read our [contributing guidelines](docs/CONTRIBUTING.md)!

Found a security vulnerability? Please refer to our [security policy](docs/SECURITY.md).

For instructions on how to set up the development environment, refer to the
[corresponding chapter](docs/CONTRIBUTING.md#development-environment).


## License

Copyright 2023 BBMRI community.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "
AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.