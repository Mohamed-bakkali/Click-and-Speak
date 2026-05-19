# Screenshots & Visual Documentation

This directory contains screenshots of the running system components for reference and documentation purposes.

## Image Files

### Workflow & Automation

- **n8n-workflow-diagram.png** — Complete workflow showing audio input → Whisper transcription → Groq LLM extraction → GLPI ticket creation → Loki logging
- **n8n-webhook-config.png** — Webhook configuration panel with test endpoint

### GLPI Dashboard

- **glpi-dashboard-overview.png** — Main GLPI dashboard showing ticket statistics (82 total), status breakdown, and trends
- **glpi-ticket-detail.png** — Individual ticket view with metadata, history, and workflow information

### Monitoring & Observability

- **grafana-loki-logs-dashboard.png** — Log aggregation dashboard showing structured logs with filtering and search
- **grafana-docker-monitoring.png** — Docker container monitoring with CPU, memory, network, and I/O metrics
- **grafana-groq-api-stats.png** — API usage statistics showing Groq Whisper and LLM model performance
- **prometheus-targets.png** — Prometheus scrape targets showing all monitored endpoints (cadvisor, n8n, tns_app, prometheus)

### Infrastructure

- **docker-desktop-containers.png** — Docker Desktop showing 11+ running containers with resource usage
- **docker-compose-services.json** — JSON representation of all services (for reference)

### Voice Interface

- **agent-vocal-ia-interface.png** — Voice-based ticket creation interface with microphone input and status indicators

## How to Use These Screenshots

Reference these images in the documentation files:

- **06-dashboard.md** — References to dashboard screenshots
- **04-n8n-workflows.md** — References to workflow and webhook screenshots
- **07-monitoring-stack.md** — References to Grafana, Prometheus, and Loki screenshots
- **08-docker-services.md** — References to Docker and container screenshots

## Format Requirements

- **Format**: PNG preferred (for lossless quality)
- **Size**: Keep under 5 MB per file
- **Resolution**: 1920x1080 or higher for readability
- **Content**: Crop to show relevant UI elements only (mask any real tokens/secrets if needed)
