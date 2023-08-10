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

| Variable name | Default value              | Description                                              |
|---------------|----------------------------|----------------------------------------------------------|
| BLAZE_URL     | http://localhost:8080/fhir | Base url of the FHIR server for sync. No trailing slash. |
