# Deployment

The application is meant to be deployed to a clean VM running Linux OS,
recommended flavor is **Ubuntu**, specifically **version 22.04**.
The main chosen method of deployment is a docker container due to its robustness. In theory, it is possible to run
it as a standalone python package.

List of supported Linux flavors:

- Ubuntu 22.04

## Prerequisites:

List of prerequisites for running the application on one of the supported operating systems:

- [Docker engine v24.0.0](https://docs.docker.com/engine/release-notes/24.0/#2400)
- [Docker compose v2.20](https://docs.docker.com/compose/release-notes/#2200)

## Docker deployment

Inside the container, the application runs under a non-root user as an additional security measure.
For deploying to production,
configure the application using environment variables (documentation bellow),
mount the directory containing patient records/data and run the following command:

```shell
docker compose --profile prod up -d
```

This will pull the latest image and start the application. To check the logs run:

```shell
docker logs fhir-module -f
```

if connection to the Blaze was successful, you should see the following line:

` Starting sync with Blaze 🔥!`
### Environment variables

The FHIR module is configured via environment variables, all of which can be found below. To override the default value,
simply specify them in `compose.yaml` in the environment section.

| Variable name                 | Default value                                          | Description                                                                                                                                                        |
|-------------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BLAZE_URL                     | http://localhost:8080/fhir                             | Base url of the FHIR server for sync. No trailing slash.                                                                                                           |
| MIABIS_BLAZE_URL              | http://localhost:5432/fhir                             | Base url of the FHIR server for syncing specifically the MIABIS on FHIR profile. No trailing slash.                                                                |
| BLAZE_USER                    | _empty_                                                | Basic auth username for accessing the blaze store via HTTP.                                                                                                        |
| MIABIS_ON_FHIR                | False                                                  | Flag allowing users to start the FHIR-module with/without newest MIABIS on FHIR profile.(pilot implementation of the new profile, False for production)            |
| STANDARDISED                  | False                                                  | Flag specifying if the material types are already standardized into MIABIS values or not.                                                                          |
| BLAZE_PASS                    | _empty_                                                | Basic auth password for accessing the blaze store via HTTP.                                                                                                        |
| PARSING_MAP_PATH              | /opt/fhir-module/default_map.json                      | Path to a JSON file containing object parsing mappings. Example [here](../util/default_map.json).                                                                  |
| MATERIAL_TYPE_MAP_PATH        | /opt/fhir-module/default_material_type_map.json        | Path to a JSON file containing mappings between organizational and FHIR material types. Example [here](../util/default_material_type_map.json).                    |
| MIABIS_MATERIAL_TYPE_MAP_PATH | /opt/fhir-module/default_miabis_material_type_map.json | Path to a JSON file containing mappings between organizational and MIABIS on FHIR material types. Example [here](../util/default_miabis_material_type_map.json)    |
| SAMPLE_COLLECTIONS_PATH       | /opt/fhir-module/default_sample_collection.json        | Path to a JSON file containing information about Sample collections. Example [here](../util/default_sample_collection.json).                                       |
| BIOBANK_PATH                  | /opt/fhir-module/default_biobank.json                  | Path to a JSON file containing information about Biobank. Example [here](..util/default_biobank.json)                                                              |
| STORAGE_TEMP_MAP_PATH         | /opt/fhir-module/default_storage_temp_map.json         | Path to a JSON file containing mapping between organizational and FHIR storage temperature. Example [here](../util/default_storage_temp_map.json).                 |
| MIABIS_STORAGE_TEMP_MAP_PATH  | /opt/fhir-module/default_miabis_storage_temp_map.json  | Path to a JSON file containing mapping between organizational and MIABIS on FHIR storage temperature. Example [here](../util/default_miabis_storage_temp_map.json) |
| TYPE_TO_COLLECTION_MAP_PATH   | /opt/fhir-module/default_type_to_collection_map.json   | Path to a JSON file containig mapping of attribute (provided in the PARSING_MAP) to a collection.  Example [here](../util/default_type_to_collection_map.json).    |
| DIR_PATH                      | /mock_dir/                                             | Path to a folder containing file(s) with records.                                                                                                                  |
| RECORDS_FILE_TYPE             | xml                                                    | Type of files containing the records.                                                                                                                              |
| CSV_SEPARATOR                 | ;                                                      | Separator used inside csv file, if the records are in a csv format.                                                                                                |
| NEW_FILE_PERIOD_DAYS          | 30                                                     | Specifies the number of days for the next upload of record file(s).                                                                                                |
| SMTP_HOST                     | localhost                                              | Specifies hostname or IP address of the SMTP server used for sending notification mails about freshness of records.                                                |
| SMTP_PORT                     | 1025                                                   | Port number sued to connect to the SMTP server for sending notification mails about fresshnes of records.                                                          |
| EMAIL_RECEIVER                | test@example.com                                       | Mail address that the notification emails will be send to.                                                                                                         |
| LOG_LEVEL                     | INFO                                                   | minimum severity of logs to be recorded. values are : INFO, DEBUG,ERROR                                                                                            |

## Object mapping

The FHIR module uses dynamically configurable maps currently stored as json files
to parse XML or CSV into Python objects. 