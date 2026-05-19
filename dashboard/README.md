# Dashboard

Sample Go web application from Grafana Monitoring Workshop. Serves as a test target for the monitoring stack.

## Overview

**Purpose**: Demonstrate monitoring of a real application

**Language**: Go 1.13

**Port**: 80 (in Docker) or 8888 (local)

## Running

### In Docker (Recommended)

```bash
docker-compose -f ../infra/tutorial-environment-docker-compose.yml up -d app
```

Access: http://localhost

### Local Build

```bash
cd app

# Build
go build -o app main.go

# Run
./app :8888

# Access
http://localhost:8888
```

## Application Features

- HTTP server with Prometheus metrics export
- MySQL database integration
- HTML template rendering
- Sample monitoring dashboard
- Includes log simulator for Loki testing

## Monitoring Integration

### Metrics Endpoint

```
GET /metrics
```

Returns Prometheus-format metrics:
- HTTP request latency
- HTTP request count by status
- Database connection stats

### Grafana Dashboards

Pre-built dashboards in `../infra/grafana/dashboards/`:

- `docker-monitoring.json` — Container resource metrics
- `n8n-glpi-monitor.json` — Workflow metrics
- `groq-api-stats.json` — API call tracking

### Log Simulation

Generate test logs:

```bash
python app/loki/web-server-logs-simulator.py
```

## File Structure

```
dashboard/
├── app/
│   ├── main.go                  # Application source code
│   ├── go.mod                   # Go module definition
│   ├── go.sum                   # Dependency checksums
│   ├── Dockerfile               # Container definition
│   ├── index.html.tmpl          # HTML template
│   ├── app                      # Compiled binary (git-ignored)
│   └── loki/
│       └── web-server-logs-simulator.py  # Test log generator
└── align-convertx/
    └── index.html               # Static HTML (unclear use)
```

## Troubleshooting

### Port 80 requires root/admin

```bash
# Linux/macOS
sudo ./app

# Windows
# Run terminal as Administrator
```

### Can't connect to MySQL

```bash
# Verify MySQL is running
docker ps | grep mysql

# Test from app container
docker-compose exec app ping db
```

### No metrics in Prometheus

```bash
# Check metrics endpoint
curl http://localhost/metrics

# Verify Prometheus targets
http://localhost:9090/targets
```

See [../docs/06-dashboard.md](../docs/06-dashboard.md) for complete documentation.
