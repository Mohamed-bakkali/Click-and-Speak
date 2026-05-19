# Dashboard

## Overview

The dashboard provides real-time visibility into the system through multiple interfaces:

1. **Voice-Based Ticket Creation Interface** — Audio input for hands-free ticket submission
2. **Grafana Monitoring Dashboard** — Real-time metrics and visualization
3. **Sample Go Application** — Test target for monitoring (from Grafana Workshop)

## Voice-Based Ticket Interface (Agent Vocal IA)

### What It Is

A dedicated web interface that allows users to create GLPI tickets by speaking. The interface:
- Captures audio input via microphone
- Sends audio to the n8n webhook (`/nouveau-ticket`)
- Provides real-time feedback on ticket creation status
- Shows transcribed text and extracted ticket metadata

**Access**: http://localhost (when dashboard app is running)

See [agent-vocal-ia-interface.png](screenshots/agent-vocal-ia-interface.png) for the interface layout.

### How It Works

1. User clicks microphone icon
2. Browser captures audio in WebM format
3. Audio sent to n8n webhook
4. Workflow processes: audio → transcription → LLM extraction → GLPI creation
5. Response displayed in UI with ticket number and status

## Monitoring Dashboard Application

**Purpose**: Demonstrate monitoring of a real application with metrics, logging, and traces.

**Location**: `dashboard/app/`

## Technology Stack

- **Language**: Go 1.13
- **Web Framework**: Standard library `net/http`
- **Metrics**: Prometheus client
- **Logging**: Structured logging (go-kit)
- **Deployment**: Docker (Alpine 3.9)

## Building & Running

### Local Build

```bash
cd dashboard/app

# Build binary (requires Go 1.13+)
go build -o app main.go

# Run locally
./app http://localhost:9001
```

This starts a web server on port 9001 (or specified port).

### Docker Build

```bash
cd dashboard/app

# Build Docker image
docker build -t monitoring-workshop-app:latest .

# Run container
docker run -p 80:80 monitoring-workshop-app:latest
```

The Dockerfile:
- Uses Alpine 3.9 as base (minimal image)
- Adds compiled `app` binary
- Adds HTML template
- Exposes port 80
- Runs with database connection to `db` service

### Via Docker Compose

Already included in `infra/tutorial-environment-docker-compose.yml`:

```yaml
app:
  build: ../../dashboard/app/  # Build from Dockerfile
  ports:
    - "80:80"
  depends_on:
    - db
```

Start with:

```bash
docker-compose -f infra/tutorial-environment-docker-compose.yml up -d app
```

## Application Architecture

### Main Components

**main.go**:
- HTTP server listening on port 80
- Connects to MySQL database (`db` service)
- Serves HTML template (`index.html.tmpl`)
- Exposes `/metrics` endpoint for Prometheus

**index.html.tmpl**:
- HTML template rendered by server
- Shows application status
- Displays database info
- Real-time monitoring dashboard

**loki/web-server-logs-simulator.py**:
- Python script to simulate log entries
- Sends logs to Loki
- Used for testing log aggregation

### Data Sources

The app reads from a database service:

```go
db, err := sql.Open("mysql", "root:password@tcp(db:3306)/monitoring")
```

It connects to MySQL container named `db` (defined in docker-compose).

## Monitoring Integration

### Prometheus Metrics

The app exports metrics at `/metrics`:

```
http://localhost/metrics
```

**Available Metrics**:
- `http_request_duration_seconds` — Request latency
- `http_requests_total` — Total requests by status code
- `database_connections_active` — Active DB connections
- Custom app metrics (from `github.com/grafana/tns/client`)

### Grafana Dashboards

Two pre-built dashboards reference this app:

1. **docker-monitoring.json** — Container metrics (CPU, memory, I/O)
2. **groq-api-stats.json** — API call tracking

### Loki Log Simulation

The app includes a log simulator:

```python
# dashboard/app/loki/web-server-logs-simulator.py
```

This script sends synthetic logs to Loki for testing log queries.

## Web Interface

Access at http://localhost/

Shows:
- Application status (running, uptime)
- Database connection info
- Request statistics
- Monitoring setup confirmation

## Development

### Project Structure

```
dashboard/
├── app/
│   ├── main.go                      # Application entry point
│   ├── go.mod                       # Go module dependencies
│   ├── go.sum                       # Dependency checksums
│   ├── Dockerfile                   # Container image definition
│   ├── index.html.tmpl              # HTML template
│   ├── app                          # Compiled binary (git-ignored)
│   └── loki/
│       └── web-server-logs-simulator.py  # Log simulator
└── align-convertx/
    └── index.html                   # Static HTML (unclear purpose)
```

### Dependencies

From `go.mod`:

```
github.com/go-kit/kit v0.10.0
github.com/grafana/tns v0.0.0-20200211161301-47c17cb38f5a
github.com/weaveworks/common v0.0.0-20200206153930-760e36ae819a
```

To update dependencies:

```bash
cd dashboard/app
go get -u
go mod tidy
```

### Adding Features

To extend the app:

1. Edit `main.go`
2. Add new HTTP handlers
3. Add metrics collection
4. Add logging
5. Rebuild: `go build -o app main.go`
6. Test: `./app`

Example new handler:

```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
})
```

## Troubleshooting

### App Won't Start

**Error**: `address already in use`

**Solution**:
```bash
# Port 80 requires admin/root privileges
sudo ./app  # macOS/Linux
# or use different port:
./app :8888
```

### Can't Connect to Database

**Error**: `Can't connect to MySQL server`

**Solution**:
```bash
# Check MySQL container is running
docker ps | grep mysql

# Check network connectivity
docker-compose exec app ping db
```

### Metrics Not Showing

**Error**: Prometheus scrapes but no data

**Solution**:
1. Check app is responding: `curl http://localhost/metrics`
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify job name matches: `job_name: "tns_app"`

## Performance Characteristics

### Resource Usage

- **CPU**: < 5% idle
- **Memory**: ~10-20 MB
- **Disk**: < 50 MB (binary + dependencies)

### Scalability

Single instance handles ~1000 req/sec. For higher load:

1. Run multiple app containers
2. Use load balancer (nginx, HAProxy)
3. Add request queue (Redis)
4. Implement caching

## Related Documentation

- [07-monitoring-stack.md](07-monitoring-stack.md) — How this app is monitored
- [08-docker-services.md](08-docker-services.md) — Docker Compose configuration

---

For local setup, see [02-installation.md](02-installation.md).
