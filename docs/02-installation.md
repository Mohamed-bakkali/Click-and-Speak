# Installation

## Prerequisites

Before starting, ensure you have:

1. **Docker Desktop** (Windows, macOS, or Docker Engine on Linux)
   - Windows/macOS: https://www.docker.com/products/docker-desktop/
   - Linux: https://docs.docker.com/engine/install/

2. **Docker Compose** (usually included with Docker Desktop)
   - Verify: `docker-compose --version`

3. **Groq API Key** (free account required)
   - Sign up: https://console.groq.com/
   - Create API key in dashboard
   - Keep it safe (you'll need it during configuration)

4. **Git** (to clone this repository)
   - https://git-scm.com/

5. **Available Ports**:
   - 8080 (GLPI)
   - 5678 (n8n)
   - 3000 (Grafana)
   - 9090 (Prometheus)
   - 3100 (Loki)
   - 9080 (Promtail)

## Step-by-Step Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd glpi-n8n-dashboard
```

### 2. Create Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```bash
# .env
GROQ_API_KEY=gsk_your_actual_key_here
GLPI_HOST=localhost
GLPI_PORT=8080
N8N_PORT=5678
GRAFANA_ADMIN_PASSWORD=your_secure_password
LOKI_RETENTION_DAYS=7
```

**Important**: Never commit `.env` to git. It's in `.gitignore` for safety.

See [03-configuration.md](03-configuration.md) for all available variables.

### 3. Start GLPI Stack

The GLPI stack includes GLPI application and MySQL database:

```bash
docker-compose -f infra/glpi-docker-compose.yml up -d
```

Wait for containers to start (20-30 seconds):

```bash
docker-compose -f infra/glpi-docker-compose.yml logs -f glpi
```

When you see something like `ready to handle connections`, GLPI is ready.

### 4. Access GLPI

Open in browser: **http://localhost:8080**

Default credentials:
- Username: `glpi`
- Password: `glpi` (or check your environment)

**First-time setup**:
1. Log in
2. Go to Setup → General
3. Configure GLPI base URL: `http://localhost:8080`
4. Go to Setup → Authentication → API → Enable REST API
5. Create API client:
   - Setup → Authentication → API Clients
   - Create new client
   - Generate App-Token
   - Keep token safe (you'll need it for n8n configuration)

### 5. Start Monitoring Stack (Optional but Recommended)

The monitoring stack includes n8n, Prometheus, Grafana, Loki, Promtail, and sample app:

```bash
docker-compose -f infra/tutorial-environment-docker-compose.yml up -d
```

Wait for all services:

```bash
docker-compose -f infra/tutorial-environment-docker-compose.yml logs -f
```

### 6. Configure n8n Workflows

Open n8n: **http://localhost:5678**

**First time**:
1. Create account and workspace
2. Go to Workflows → Import from File
3. Select `n8n/workflows/workflows.json`
4. Two workflows will be imported:
   - "My workflow"
   - "Click & Speak ITSM"

**Configure Credentials**:

For each workflow, you need to set up credentials for:

1. **Groq API**:
   - In n8n: Settings → Credentials → New credential
   - Type: `HTTP Custom Auth` or `Groq API`
   - Add your Groq API key from step 2
   - Save

2. **GLPI**:
   - Already configured with hardcoded values in workflow (DEMO ONLY)
   - For production: Change to use environment variables or credentials store
   - Current auth: `Basic` encoded `glpi:glpi`
   - Header: `Session-Token` from GLPI `/initSession` response

See [04-n8n-workflows.md](04-n8n-workflows.md) for detailed workflow configuration.

### 7. Access All Services

Once everything is running:

| Service | URL | Default Login |
|---------|-----|---|
| GLPI | http://localhost:8080 | glpi / glpi |
| n8n | http://localhost:5678 | Set during first launch |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | No auth |
| Loki | http://localhost:3100 | No auth |

### 8. Test the Workflow

**Send a test audio request to n8n**:

```bash
curl -X POST http://localhost:5678/webhook/nouveau-ticket \
  -F "audio=@sample-audio.wav" \
  -F "name=Test User" \
  -F "description=Test issue"
```

Or use the n8n UI to manually trigger the webhook.

**Verify**:
1. Check n8n execution history: see if workflow ran
2. Check GLPI: new ticket should appear in queue
3. Check Grafana Loki dashboard: see log entries

### 9. Verify Monitoring Setup

**Check Prometheus targets**:

Go to http://localhost:9090/targets

You should see:
- `tns_app` (TNS sample app)
- `prometheus` (Prometheus itself)
- `n8n` (n8n metrics endpoint)
- `cadvisor` (Docker monitoring)

**Check Grafana dashboards**:

Go to http://localhost:3000 → Dashboards

Pre-provisioned dashboards:
- `docker-monitoring.json` — Docker container metrics
- `groq-api-stats.json` — Groq API call tracking
- `n8n-glpi-monitor.json` — Workflow and GLPI metrics

## Troubleshooting Setup

### Ports Already in Use

If Docker fails to start a service due to port conflict:

```bash
# Find what's using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows
```

Either:
- Stop the conflicting service
- Change port mapping in `docker-compose.yml`: `8081:80` instead of `8080:80`

### Docker Compose Not Found

If you get `command not found: docker-compose`:

Try `docker compose` (v2 syntax):

```bash
docker compose -f infra/glpi-docker-compose.yml up -d
```

### Can't Connect to GLPI from n8n

Inside Docker, use container names, not `localhost`:

- From outside Docker: `http://localhost:8080`
- From inside Docker (n8n): `http://host.docker.internal:8080` (Windows/macOS) or `http://glpi:80` (Linux)

Workflow is pre-configured with `host.docker.internal`.

### MySQL Connection Fails

If MySQL won't start or GLPI can't connect:

```bash
# Check MySQL logs
docker logs glpi-db-1

# Common issue: MySQL initializing for first time, wait 30 seconds
```

### Out of Memory

Loki and Prometheus can consume significant RAM, especially on systems with <4GB:

```bash
# Limit Loki to 512MB
docker update --memory 512m tutorial-environment_loki_1
```

## Clean Up

### Stop All Services

```bash
docker-compose -f infra/glpi-docker-compose.yml down
docker-compose -f infra/tutorial-environment-docker-compose.yml down
```

### Remove Volumes (WARNING: Deletes Data)

⚠️ This deletes all data stored in containers:

```bash
# Only if you want to reset everything
docker-compose -f infra/glpi-docker-compose.yml down -v
docker-compose -f infra/tutorial-environment-docker-compose.yml down -v
```

### Start Fresh

If you need a completely clean state:

```bash
# Stop and remove volumes
docker-compose -f infra/glpi-docker-compose.yml down -v
docker-compose -f infra/tutorial-environment-docker-compose.yml down -v

# Remove `.env` and recreate
rm .env
cp .env.example .env
# Edit .env with new configuration

# Restart
docker-compose -f infra/glpi-docker-compose.yml up -d
docker-compose -f infra/tutorial-environment-docker-compose.yml up -d
```

## Next Steps

- [03-configuration.md](03-configuration.md) — Detailed environment variable reference
- [04-n8n-workflows.md](04-n8n-workflows.md) — Import and customize workflows
- [09-troubleshooting.md](09-troubleshooting.md) — Common issues and fixes
