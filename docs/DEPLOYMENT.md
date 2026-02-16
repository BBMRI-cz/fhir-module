# Deployment

The application is meant to be deployed to a clean VM running Linux OS,
recommended flavor is **Ubuntu**, specifically **version 22.04**.
The main chosen method of deployment is a docker container due to its robustness.
The app can be deployed in different configurations, specifically:

- only fhir-module container responsible for the transformation
- fhir-module + UI for setup and management in separate containers
- fhir-module + UI in combined container
- any of the above + monitoring functionality

In theory, it is possible to run it as a standalone python package.

List of supported Linux flavors:

- Ubuntu 22.04

## Prerequisites:

List of prerequisites for running the application on one of the supported operating systems:

- [Docker engine v24.0.0](https://docs.docker.com/engine/release-notes/24.0/#2400)
- [Docker compose v2.20](https://docs.docker.com/compose/release-notes/#2200)

## Docker deployment

Inside the container, the application runs under a non-root user as an additional security measure.
For deploying to production,
configure the application using environment variables and modify the config-file (documentation bellow),
mount the directory containing patient records/data and run the following command:

```shell
docker compose --profile prod up -d
```

The supported profiles are:

```shell
--profile prod
--profile combined
--profile ui --profile prod # for separate deployment of UI & fhir-module (not recommended)
--profile monitoring # to be added to the other profiles to enable monitoring
```

A complete example is then:

```shell
docker compose --profile combined --profile monitoring up -d
```

This will pull the latest image and start the application. To check the logs run:

```shell
docker logs fhir-module -f
```

if connection to the Blaze was successful, you should see the following line:

` Starting sync with Blaze 🔥!`

#### First-time Setup

On first deployment, the UI will automatically:

1. Initialize the SQLite database
2. Create default user accounts
3. Set up authentication system

**Important**: Make sure to set the `NEXTAUTH_SECRET` environment variable to a secure random string in production environments.

### Environment variables

The FHIR module is configured via environment variables, all of which can be found below. These values **MUST** be present on the .env file in the same folder as the `compose.yaml` file.

| Variable name        | Required                       | Default value              | Description                                                                                                                                                                        |
| -------------------- | ------------------------------ | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BLAZE_URL            | true                           | http://localhost:8080/fhir | Base url of the FHIR server for sync. No trailing slash. When deployed in container, localhost is replaced by the blaze container name.                                            |
| MIABIS_BLAZE_URL     | false (true if MIABIS_ON_FHIR) | http://localhost:5432/fhir | Base url of the FHIR server for syncing specifically the MIABIS on FHIR profile. No trailing slash. When deployed in container, localhost is replaced by the blaze container name. |
| MIABIS_ON_FHIR       | false                          | False                      | Flag allowing users to start the FHIR-module with/without newest MIABIS on FHIR profile.(pilot implementation of the new profile, False for production)                            |
| BLAZE_USER           | false                          | _empty_                    | Basic auth username for accessing the blaze store via HTTP.                                                                                                                        |
| BLAZE_PASS           | false                          | _empty_                    | Basic auth password for accessing the blaze store via HTTP.                                                                                                                        |
| NEW_FILE_PERIOD_DAYS | false                          | 30                         | Specifies the number of days for the next upload of record file(s).                                                                                                                |
| SMTP_HOST            | false                          | localhost                  | Specifies hostname or IP address of the SMTP server used for sending notification mails about freshness of records.                                                                |
| SMTP_PORT            | false                          | 1025                       | Port number sued to connect to the SMTP server for sending notification mails about fresshnes of records.                                                                          |
| EMAIL_RECEIVER       | false                          | test@example.com           | Mail address that the notification emails will be send to.                                                                                                                         |
| LOG_LEVEL            | false                          | INFO                       | minimum severity of logs to be recorded. values are : INFO, DEBUG,ERROR                                                                                                            |

### Fhir module setup

To allow the setup modification while running the subset of change-prone variables are specified in `/util/shared_config.json`. This file is pre-seeded with some default values, but to work properly, adjustments need made per-deployment.

**Important**: The `shared_config.json` file is mounted as a bind mount from your host system into the container. This means:

- **Directly Editable**: You can edit `util/shared_config.json` on your host machine using any text editor
- **Immediate Updates**: The application reads directly from this bind-mounted file, so your changes are immediately available (config is reloaded on next access)
- **No Container Rebuild**: No need to rebuild the image or exec into the container to make configuration changes
- **UI Integration**: The web UI can also modify this file programmatically, and changes will be reflected on your host system
- **Persistent**: Changes persist across container restarts since the file lives on your host

| Variable name                 | Required                                   | Default value                                          | Description                                                                                                                                                        |
| ----------------------------- | ------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PARSING_MAP_PATH              | false (can be set by the UI)               | /opt/fhir-module/default_map.json                      | Path to a JSON file containing object parsing mappings. Example [here](../util/default_map.json).                                                                  |
| MATERIAL_TYPE_MAP_PATH        | false (can be set by the UI)               | /opt/fhir-module/default_material_type_map.json        | Path to a JSON file containing mappings between organizational and FHIR material types. Example [here](../util/default_material_type_map.json).                    |
| MIABIS_MATERIAL_TYPE_MAP_PATH | false (can be set by the UI)               | /opt/fhir-module/default_miabis_material_type_map.json | Path to a JSON file containing mappings between organizational and MIABIS on FHIR material types. Example [here](../util/default_miabis_material_type_map.json)    |
| SAMPLE_COLLECTIONS_PATH       | false (can be set by the UI)               | /opt/fhir-module/default_sample_collection.json        | Path to a JSON file containing information about Sample collections. Example [here](../util/default_sample_collection.json).                                       |
| BIOBANK_PATH                  | true                                       | /opt/fhir-module/default_biobank.json                  | Path to a JSON file containing information about Biobank. Example [here](..util/default_biobank.json)                                                              |
| STORAGE_TEMP_MAP_PATH         | false                                      | /opt/fhir-module/default_storage_temp_map.json         | Path to a JSON file containing mapping between organizational and FHIR storage temperature. Example [here](../util/default_storage_temp_map.json).                 |
| MIABIS_STORAGE_TEMP_MAP_PATH  | false                                      | /opt/fhir-module/default_miabis_storage_temp_map.json  | Path to a JSON file containing mapping between organizational and MIABIS on FHIR storage temperature. Example [here](../util/default_miabis_storage_temp_map.json) |
| TYPE_TO_COLLECTION_MAP_PATH   | false                                      | /opt/fhir-module/default_type_to_collection_map.json   | Path to a JSON file containig mapping of attribute (provided in the PARSING_MAP) to a collection. Example [here](../util/default_type_to_collection_map.json).     |
| ROOT_DIR                      | true (can be set by the UI)                | /opt/records                                           | Path to as dir that is a root of what can be selected as RECORDS_DIR_PATH on the UI.                                                                               |
| RECORDS_DIR_PATH              | false (can be set by the UI)               | /mock_dir/                                             | Path to a folder containing file(s) with records.                                                                                                                  |
| RECORDS_FILE_TYPE             | false (can be set by the UI)               | xml                                                    | Type of files containing the records.                                                                                                                              |
| CSV_SEPARATOR                 | false (can be set by the UI, true for csv) | ;                                                      | Separator used inside csv file, if the records are in a csv format.                                                                                                |

### Monitoring and Logging Environment Variables

The following environment variables are used for configuring monitoring and logging capabilities:

| Variable name         | Default value | Description                                                                                                                                                                                 |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ENVIRONMENT           | _empty_       | Specifies the deployment environment (e.g., LOCAL, PRODUCTION, STAGING). Used for environment-specific configuration. This value is used to distinguish logs from different envs in Grafana |
| PROM_REMOTE_URL       | _empty_       | URL endpoint for pushing Prometheus metrics to a remote Prometheus server or Grafana Cloud.                                                                                                 |
| PROM_REMOTE_USER      | _empty_       | Username for authentication with the remote Prometheus metrics endpoint.                                                                                                                    |
| PROM_REMOTE_PASS      | _empty_       | Password or API key for authentication with the remote Prometheus metrics endpoint.                                                                                                         |
| GRAFANA_LOGS_URL      | _empty_       | URL for Loki to push the logs to Grafana for processing                                                                                                                                     |
| GRAFANA_LOGS_USERNAME | _empty_       | Username for authentication with Grafana Cloud logs service for centralized log aggregation.                                                                                                |
| GRAFANA_LOGS_PASSWORD | _empty_       | Password or API key for authentication with Grafana Cloud logs service for centralized log aggregation.                                                                                     |

#### UI Application Variables

The following environment variables are used to configure the Next.js UI application:

| Variable name                  | Default value                     | Description                                                                  |
| ------------------------------ | --------------------------------- | ---------------------------------------------------------------------------- |
| NODE_ENV                       | development                       | Node.js environment mode (development/production)                            |
| PORT                           | 3000                              | Port on which the UI application runs                                        |
| NEXTAUTH_SECRET                | _required_                        | Secret key for NextAuth.js session encryption. **Must be set in production** |
| AUTH_TRUST_HOST                | false                             | Set to `true` for Docker deployment to trust proxy headers                   |
| BACKEND_API_URL                | http://localhost:5000             | URL of the FHIR module backend API                                           |
| PROMETHEUS_URL                 | http://prometheus:9090            | URL of the Prometheus metrics server                                         |
| PASSWORD_MIN_LENGTH            | 8                                 | Minimum password length requirement                                          |
| PASSWORD_MAX_LENGTH            | 128                               | Maximum password length requirement                                          |
| PASSWORD_REQUIRE_UPPERCASE     | false                             | Require uppercase letters in passwords                                       |
| PASSWORD_REQUIRE_LOWERCASE     | false                             | Require lowercase letters in passwords                                       |
| PASSWORD_REQUIRE_NUMBERS       | false                             | Require numbers in passwords                                                 |
| PASSWORD_REQUIRE_SPECIAL_CHARS | false                             | Require special characters in passwords                                      |
| PASSWORD_SPECIAL_CHARS         | !@#$%^&\*()\_+-=[]{}&#124;;:,.<>? | Allowed special characters for passwords                                     |

Following can be used as a basis for the custom .env file

```shell
ENVIRONMENT=TEST
PROM_REMOTE_URL=your grafana url
PROM_REMOTE_USER=your grafana user
PROM_REMOTE_PASS=your grafana password
GRAFANA_LOGS_URL=your grafana loki endpoint
GRAFANA_LOGS_USERNAME=your grafana loki username
GRAFANA_LOGS_PASSWORD=your grafana loki password

PORT=3000
NODE_ENV=production
BACKEND_API_URL="http://localhost:5000" # If running as combined container, fhir-module container name either
PROMETHEUS_URL="http://prometheus:9090"

BLAZE_URL="http://test-blaze:8080/fhir"
MIABIS_BLAZE_URL="http://miabis-blaze:8080/fhir"

MIABIS_ON_FHIR="True"

NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET=generate your own secret, changing it will logout everyone # openssl rand -base64 32
AUTH_TRUST_HOST="true"

REGISTER_ALLOWED=false

# The password specs only important is registration is allowed
PASSWORD_MIN_LENGTH=8
PASSWORD_MAX_LENGTH=128
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
PASSWORD_SPECIAL_CHARS="!@#$%^&*()_+-=[]{}|;:,.<>?"

```

The `/util/shared_config.json` must be modified by hand if not using UI, otherwise only the required fields must be set before start.

## Object mapping

The FHIR module uses dynamically configurable maps currently stored as json files
to parse XML,CSV or JSON into Python objects.
