# Infrastructure as Code

This folder contains Docker Compose files and configuration for all services.

## Files

### glpi-docker-compose.yml

GLPI ticketing system + MySQL database stack.

**Services**:
- `glpi` — Open-source IT asset management (port 8080)
- `db` — MySQL 8.0 database

**Volumes**:
- `glpi_data` — GLPI configuration and data
- `db_data` — MySQL data

**Start**:
```bash
docker-compose -f infra/glpi-docker-compose.yml up -d
```

**Access**: http://localhost:8080 (glpi:glpi)

See [../docs/05-glpi-integration.md](../docs/05-glpi-integration.md) for details.

### tutorial-environment-docker-compose.yml

Full monitoring and automation stack.

**Services**:
- `n8n` — Workflow automation (port 5678)
- `prometheus` — Metrics collection (port 9090)
- `grafana` — Dashboards (port 3000)
- `loki` — Log aggregation (port 3100)
- `promtail` — Log shipper (port 9080)
- `app` — Sample monitoring target (port 80)

**Start**:
```bash
docker-compose -f infra/tutorial-environment-docker-compose.yml up -d
```

See [../docs/07-monitoring-stack.md](../docs/07-monitoring-stack.md) for details.

## Configuration Files

### grafana/

Grafana provisioning (auto-configured on startup).

- **provisioning/datasources/datasources.yaml** — Data source definitions (Prometheus, Loki)
- **dashboards/** — Pre-built dashboards:
  - `docker-monitoring.json` — Container metrics
  - `groq-api-stats.json` — Groq API stats
  - `n8n-glpi-monitor.json` — Workflow monitoring

### prometheus/

Prometheus metrics collection configuration.

- **prometheus.yml** — Scrape targets and intervals

Configured targets:
- n8n (localhost:5678/metrics)
- app (app:80/metrics)
- cadvisor (Docker metrics)

### promtail/

Promtail log shipper configuration.

- **config.yml** — Log collection from Docker containers

Sends logs to Loki for aggregation.

## Environment Variables

Both docker-compose files reference `.env` for sensitive values:

```yaml
environment:
  GLPI_DB_PASSWORD: ${GLPI_DB_PASSWORD}
  GROQ_API_KEY: ${GROQ_API_KEY}
```

See `../.env.example` for all variables.

## Common Operations

### View Service Status

```bash
docker-compose -f infra/glpi-docker-compose.yml ps
docker-compose -f infra/tutorial-environment-docker-compose.yml ps
```

### View Logs

```bash
docker-compose -f infra/glpi-docker-compose.yml logs -f glpi
docker-compose -f infra/tutorial-environment-docker-compose.yml logs -f n8n
```

### Stop Services

```bash
docker-compose -f infra/glpi-docker-compose.yml down
docker-compose -f infra/tutorial-environment-docker-compose.yml down
```

### Rebuild Images

```bash
docker-compose -f infra/tutorial-environment-docker-compose.yml build --no-cache
```

## Docker Compose Versions

These files use v3.8 syntax (compatible with):
- Docker Desktop 3.0+
- Docker Engine 19.03+
- Docker Compose 1.25+

## Networking

Both stacks create isolated networks:

- **glpi_default** — GLPI stack network
- **tutorial_environment_default** — Monitoring stack network

Services can reach each other by container name on their network.

For inter-stack communication, use `host.docker.internal` from containers (Windows/macOS).

## Volumes

### Named Volumes

Persistent data:
- `glpi_data` — GLPI config/plugins
- `db_data` — MySQL data

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect glpi_db_data

# Backup volume
docker run --rm -v glpi_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/glpi_data.tar.gz -C /data .
```

### Ephemeral Storage

By default, Prometheus and Loki use container-internal storage (lost on restart).

To persist, add named volumes to compose file and restart.

## Advanced Configuration

### Add Health Checks

```yaml
services:
  glpi:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Resource Limits

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
```

### Logging Configuration

```yaml
services:
  n8n:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## Troubleshooting

### Port Conflicts

```bash
# Find service using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows
```

Solution: Change port mapping or stop conflicting service.

### Network Issues

```bash
# Check network
docker network inspect glpi_default

# Test connectivity between containers
docker-compose exec glpi ping db
```

### Container Won't Start

```bash
# Check logs
docker-compose logs <service>

# Rebuild
docker-compose build --no-cache <service>
docker-compose up -d <service>
```

---

See [../docs/08-docker-services.md](../docs/08-docker-services.md) for complete documentation.
