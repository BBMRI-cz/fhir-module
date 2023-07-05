# FHIR module [![codecov](https://codecov.io/gh/BBMRI-cz/fhir-module/branch/master/graph/badge.svg?token=3eklJNhIS5)](https://codecov.io/gh/BBMRI-cz/fhir-module) [![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
## Goal
The goal of this project is to create a data integration tool for biobanks that are a part of the BBMRI Federated Search platfrom.
## State
Supports syncing of patients between a [Blaze FHIR store](https://github.com/samply/blaze) and an XML file repository. Currently, the XML files must have the same structure as this [test file](./test/xml_data/MMCI_1.xml).
## Development
_Instructions on how to contribute to the development._

### Development environment set up
_**Python Interpreter:**_ 3.11

[Blaze store as a docker container](https://github.com/samply/blaze#docker)

[BlazeCTL](https://github.com/samply/blazectl): a command line tool for interacting with a Blaze store

[FHIR Test data generator](https://github.com/samply/bbmri-fhir-gen): a command line tool for generating FHIR test data according to the [BBMRI.de FHIR profile](https://simplifier.net/bbmri.de).