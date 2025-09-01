# Monitoring Setup

This project uses **Prometheus** for uptime metrics collection and **Promtail** to push logs regarding the app status to Grafana Cloud. The monitoring stack is integrated with the FHIR module to provide observability mainly for the synchronization processes, since that is the main purpose of the module.

## Overview

The monitoring setup consists of:

- **Prometheus**: Collects metrics from the FHIR module application
- **Promtail**: Aggregates and forwards logs to Grafana Cloud (Loki)
- **Configuration Templates**: Template files with environment variable substitution
- **Automatic config creation (optional)**: There is a container responsible for filling out the templates from the environment variables, in case this process is not preformed manually

## Enabling monitoring

To enable monitoring containers use the `monitoring` profile for docker compose call.

```bash
# Run the prod profile with the monitoring included
docker compose --profile monitoring --profile prod up

```

### Monitoring Setup Methods

**The following variables need to be manually substituted to the config files [(also described here)](/docs/DEPLOYMENT.md)**

| Variable name         | Default value | Description                                                                                                                                                                                 |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ENVIRONMENT           | _empty_       | Specifies the deployment environment (e.g., LOCAL, PRODUCTION, STAGING). Used for environment-specific configuration. This value is used to distinguish logs from different envs in Grafana |
| PROM_REMOTE_URL       | _empty_       | URL endpoint for pushing Prometheus metrics to a remote Prometheus server or Grafana Cloud.                                                                                                 |
| PROM_REMOTE_USER      | _empty_       | Username for authentication with the remote Prometheus metrics endpoint.                                                                                                                    |
| PROM_REMOTE_PASS      | _empty_       | Password or API key for authentication with the remote Prometheus metrics endpoint.                                                                                                         |
| GRAFANA_LOGS_URL      | _empty_       | Url for the loki endpoint to push logs to Grafana cloud                                                                                                                                     |
| GRAFANA_LOGS_USERNAME | _empty_       | Username for authentication with Grafana Cloud logs service for centralized log aggregation.                                                                                                |
| GRAFANA_LOGS_PASSWORD | _empty_       | Password or API key for authentication with Grafana Cloud logs service for centralized log aggregation.                                                                                     |

#### Manual Setup

Manually copy and configure the template files:

1. **Copy Prometheus configuration:**

   ```bash
   # Copy template to Prometheus container
   docker cp config/prometheus.template.yml <prometheus-container>:/etc/prometheus/prometheus.yml

   # Manually substitute environment variables in the file as described above

   # Restart Prometheus
   docker restart <prometheus-container>
   ```

2. **Copy Promtail configuration:**

   ```bash
   # Copy template to Promtail container
   docker cp config/promtail-config.template.yaml <promtail-container>:/etc/promtail/promtail-config.yaml

   # Manually substitute environment variables in the file as described above

   # Restart Promtail
   docker restart <promtail-container>
   ```

### Grafana cloud setup

#### Prometheus setup

1. Open the grafana cloud interface for the given stack
2. On the left side, select **Data sources**
3. Select **Add new Datasource**
4. Select **Prometheus**
5. Setup the datasource
6. Copy the **URL**, **Username** and **Password** to their respective environment variables as described above

#### Promtail env variables acquisition

1. Login to your Grafana cloud account
2. Access the **My Account** page
3. On the left side under the **Grafana cloud** access your stack (if non-existent create it)
4. Find the **Loki**
5. Click **details**
6. Locate the **Using Grafana with Logs** section
7. The **URL** and **User** should be used for **GRAFANA_LOGS_URL** and **GRAFANA_LOGS_USERNAME**
8. Under **Password** create a new token for **GRAFANA_LOGS_PASSWORD**
