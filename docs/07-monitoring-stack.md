# Monitoring Stack

## Overview

The monitoring stack collects metrics, logs, and traces from all services and provides visualization through Grafana.

**Components**:
- **Prometheus** — Metrics collection (time-series database)
- **Grafana** — Dashboards and visualization
- **Loki** — Log aggregation
- **Promtail** — Log shipper
- **cAdvisor** — Docker container metrics

## Architecture

```
Data Sources (n8n, app, GLPI, Docker)
    ↓
Prometheus Scraper (pulls metrics)  +  Promtail (ships logs)
    ↓                                    ↓
Prometheus (metrics storage)  +  Loki (log storage)
    ↓                              ↓
        Grafana (queries both)
        ↓
    Dashboards & Alerts
```

## Prometheus

### Purpose

Prometheus is a time-series database that stores metrics from applications and infrastructure.

### Configuration

See `infra/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "tns_app"
    scrape_interval: 5s
    static_configs:
      - targets: ["app:80"]

  - job_name: "n8n"
    scrape_interval: 15s
    static_configs:
      - targets: ["host.docker.internal:5678"]
    metrics_path: /metrics

  - job_name: "cadvisor"
    scrape_interval: 10s
    static_configs:
      - targets: ["cadvisor:8080"]
```

### Scrape Targets

| Job | Endpoint | Interval | Metrics |
|-----|----------|----------|---------|
| `tns_app` | app:80/metrics | 5s | HTTP requests, latency, DB connections |
| `n8n` | localhost:5678/metrics | 15s | Workflow executions, success rate |
| `cadvisor` | cadvisor:8080/metrics | 10s | Container CPU, memory, I/O |
| `prometheus` | localhost:9090/metrics | 15s | Prometheus own metrics |

### Accessing Prometheus

**Web UI**: http://localhost:9090

**Visual Reference**: See the screenshots in `docs/screenshots/` for monitoring dashboards and container views.

**Query Examples**:
```
# HTTP request latency (p95)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Failed requests in last hour
increase(http_requests_total{status=~"5.."}[1h])

# Container memory usage
container_memory_usage_bytes{container_label_com_docker_compose_service=~"glpi|n8n"}
```

### Data Retention

Default: 30 days (configured in docker-compose)

To change:

```yaml
command:
  - "--storage.tsdb.retention.time=60d"  # Keep 60 days instead
```

## Grafana

### Purpose

Grafana queries Prometheus and Loki to display dashboards, graphs, and alerts.

### Accessing Grafana

**Web UI**: http://localhost:3000

**Default Credentials**:
- Username: `admin`
- Password: `admin` (or configured in .env)

### Available Dashboards

The system includes four pre-configured dashboards:

#### 1. Docker Monitoring Dashboard

**Visual Reference**: See [grafana-docker-monitoring.png](screenshots/grafana-docker-monitoring.png)

**Metrics Shown**:
- CPU usage across all containers (33.9% total)
- Memory usage breakdown by service (5.34 GiB total)
- Network I/O per container
- Container uptime and health
- Resource limits and allocation

**Use Case**: Monitor resource consumption of GLPI, n8n, databases, and monitoring stack itself.

#### 2. Groq API Statistics Dashboard
**Metrics Shown**:
- Whisper model availability (Audio 71 models available)
- LLM model usage and inference time
- API call frequency and distribution
- Available models and their capacity

**Use Case**: Track Groq API usage, model switching, and performance trends.

#### 3. n8n Workflow Monitoring

**Dashboard File**: `infra/grafana/dashboards/n8n-glpi-monitor.json`

**Metrics Tracked**:
- Workflow execution count and success rate
- Average execution duration
- Error frequency by node type
- GLPI ticket creation throughput

#### 4. Application Logs (Loki)

**Visual Reference**: See [grafana-loki-logs-dashboard.png](screenshots/grafana-loki-logs-dashboard.png)

**Shown**:
- Structured logs from all services
- Log filtering by service, level, and timeframe
- Recent log volume trends (last 24 hours)
- JSON log parsing and field extraction

**Use Case**: Troubleshoot workflow failures, debug API errors, and audit ticket creation events.

### Provisioning

On startup, Grafana auto-provisions:

1. **Data Sources**:
   - Prometheus at http://prometheus:9090
   - Loki at http://loki:3100

2. **Dashboards**:
   - `docker-monitoring.json` — Container metrics
   - `groq-api-stats.json` — Groq API stats
   - `n8n-glpi-monitor.json` — Workflow monitoring

See `infra/grafana/provisioning/` for configuration files.

### Creating Custom Dashboards

1. Go to Grafana → **Dashboards** → **New**
2. Add panels by clicking **Add Panel**
3. Select data source (Prometheus or Loki)
4. Write query (e.g., `rate(http_requests_total[5m])`)
5. Configure visualization (graph, table, stat, etc.)
6. Save dashboard

### Key Metrics to Monitor

**Application Health**:
```
http_requests_total  # Total requests
http_request_duration_seconds  # Latency
http_requests_total{status=~"5.."}  # Errors
```

**Infrastructure**:
```
container_cpu_usage_seconds_total  # CPU
container_memory_usage_bytes  # Memory
container_network_transmit_bytes  # Network
```

**Workflow Success**:
```
n8n_workflow_execution_success  # Successful workflows
n8n_workflow_execution_failed  # Failed workflows
```

## Loki

### Purpose

Loki is a log aggregation system optimized for container environments.

**Advantages over traditional logging**:
- Uses Kubernetes labels instead of full-text indexing (lower resource usage)
- Integrates seamlessly with Grafana
- Great for container logs

### Configuration

See `infra/promtail/config.yml`:

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker-containers
    static_configs:
      - targets: [localhost]
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*-json.log
```

### Sending Logs to Loki

From applications:

```bash
# Example: n8n workflow sends log
curl -X POST http://loki:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [{
      "stream": {"app": "n8n", "workflow": "ticket-creation"},
      "values": [["1234567890000000000", "Ticket created: #123"]]
    }]
  }'
```

### Querying Logs in Grafana

1. Create new dashboard
2. Add panel with data source = Loki
3. Use LogQL queries:

```
{app="n8n"}  # All logs from n8n
{app="n8n", workflow="ticket-creation"}  # Filtered logs
| json  # Parse JSON lines
| status =~ "error|failed"  # Filter by status
```

### Log Retention

Currently: Logs stored in memory (ephemeral)

To persist logs, add volume:

```yaml
volumes:
  - loki_data:/loki
```

And configure retention in `loki/config.yml`:

```yaml
limits_config:
  retention_period: 168h  # Keep 7 days
```

## Promtail

### Purpose

Promtail ships logs from containers to Loki.

### Configuration

See `infra/promtail/config.yml`:

- Listens on port 9080
- Reads Docker container logs from `/var/lib/docker/containers/`
- Pushes to Loki at `http://loki:3100`

### Supported Log Sources

- Docker container logs (JSON format)
- Syslog
- Local files

To add new source:

```yaml
scrape_configs:
  - job_name: application-logs
    static_configs:
      - targets: [localhost]
        labels:
          job: myapp
          __path__: /var/log/myapp/*.log
```

## cAdvisor

### Purpose

Google's cAdvisor provides Docker container metrics (CPU, memory, network, I/O).

**Endpoint**: http://localhost:8080

### Metrics

```
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_network_transmit_bytes
container_memory_failcnt
```

### Limitations

- No persistent storage (metrics lost on restart)
- Local container metrics only (not cloud containers)

For production, use Prometheus Node Exporter + Docker stats instead.

## Alerting (Not Configured)

To add alerting:

1. **Create alert rules** in Prometheus

Create `infra/prometheus/alerts.yml`:

```yaml
groups:
  - name: app_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
```

2. **Configure Alertmanager** to send to:
   - Email
   - Slack
   - PagerDuty
   - Webhooks

3. **Link in Prometheus**:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]
```

## Troubleshooting Monitoring

### Prometheus Not Scraping

**Check targets**: http://localhost:9090/targets

If "DOWN":
- Verify endpoint is reachable from Prometheus container
- Check firewall/network rules
- Verify metrics endpoint exists and responds

### Loki Not Receiving Logs

```bash
# Check Promtail logs
docker logs tutorial-environment_promtail_1

# Verify Loki is running
docker logs tutorial-environment_loki_1
```

### Grafana Can't Connect to Data Sources

```bash
# From Grafana container, test connectivity
docker-compose exec grafana curl http://prometheus:9090/-/healthy
docker-compose exec grafana curl http://loki:3100/ready
```

### High Memory Usage

Loki and Prometheus can use lots of memory:

```bash
# Limit container memory
docker update --memory 1g tutorial-environment_prometheus_1
docker update --memory 512m tutorial-environment_loki_1
```

Or configure retention:

```yaml
prometheus:
  args:
    - "--storage.tsdb.retention.size=1GB"

loki:
  config:
    limits_config:
      retention_period: 24h
```

## Best Practices

1. **Set appropriate scrape intervals**: Balance between resolution and resource usage
2. **Use recording rules**: Pre-compute expensive queries
3. **Set sensible retention**: Don't keep metrics forever
4. **Monitor the monitors**: Alert if Prometheus/Loki go down
5. **Label consistently**: Use consistent label names across services
6. **Document dashboards**: Add descriptions and queries as comments

## Performance Tuning

### Prometheus

```yaml
global:
  scrape_interval: 30s  # Increase from 15s (lower resolution, less CPU)
  evaluation_interval: 30s

storage:
  tsdb:
    retention.time: 7d  # Reduce from 30d (less disk)
```

### Loki

```yaml
limits_config:
  retention_period: 24h  # Reduce from 7d (less disk)
  max_cache_age_loops: 1  # Faster queries
```

---

See [02-installation.md](02-installation.md) for setup.
See [09-troubleshooting.md](09-troubleshooting.md) for common issues.
