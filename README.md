# FHIR module

[![CI build](https://github.com/BBMRI-cz/fhir-module/actions/workflows/build.yml/badge.svg)](https://github.com/BBMRI-cz/Data-Integration-Module/actions/workflows/build.yml) [![codecov](https://codecov.io/gh/BBMRI-cz/fhir-module/branch/master/graph/badge.svg?token=3eklJNhIS5)](https://codecov.io/gh/BBMRI-cz/fhir-module) [![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-360/) [![Linter: pylint](https://img.shields.io/badge/Linter-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)

The BBMRI-ERIC FHIR module is a container based application connecting biobanks
to other IT tools and services in our ecosystem on a local level.
## Goal

The goal of this project is to create a highly customizable data integration tool for biobanks that are a
part of BBMRI-ERIC.

## State

Supports syncing of patients between a [Blaze FHIR store](https://github.com/samply/blaze) and an XML file repository.
Currently, the XML files must have the same structure as this [test file](./test/xml_data/MMCI_1.xml).

## Development

_Instructions on how to contribute to the development._

### Development environment set up

_**Python Interpreter:**_ 3.11

[Blaze store as a docker container](https://github.com/samply/blaze#docker)

[BlazeCTL](https://github.com/samply/blazectl): a command line tool for interacting with a Blaze store

[FHIR Test data generator](https://github.com/samply/bbmri-fhir-gen): a command line tool for generating FHIR test data
according to the [BBMRI.de FHIR profile](https://simplifier.net/bbmri.de).