# Project Overview

## Executive Summary

This project automates ticket creation in GLPI using audio input, AI processing, and workflow orchestration. It demonstrates:

- Integration of multiple SaaS APIs (Groq, GLPI)
- Real-time container monitoring with Prometheus and Grafana
- Workflow automation with n8n
- Log aggregation with Loki
- Docker-based local development environment

## Project Genesis

Reconstructed from recovered Docker containers and volumes. The original local environment included:
- GLPI running on Docker Desktop (Windows)
- n8n instance with exported workflows
- Monitoring/logging stack (Prometheus, Grafana, Loki, Promtail)
- A sample Go app for observability testing

This repository preserves the working configuration and intent while sanitizing it for public sharing.

## Intended Use

1. **Learning**: Understanding how to integrate GLPI with modern workflow tools and monitoring
2. **Reference**: Template for similar ITSM automation projects
3. **Local Development**: Developers can spin up a complete testing environment with one command
4. **Prototyping**: Quickly test new n8n workflows and GLPI integrations

## Key Systems

| System | Purpose | Container Port | Technology |
|--------|---------|-----------------|------------|
| GLPI | IT ticketing / asset management | 8080 | PHP + MySQL |
| n8n | Workflow automation | 5678 | Node.js |
| Prometheus | Metrics collection | 9090 | Time-series DB |
| Grafana | Dashboards & visualization | 3000 | Go + React |
| Loki | Log aggregation | 3100 | Go |
| Promtail | Log shipper | 9080 | Go |

## Data Flow

1. **User speaks into audio input** (HTTP POST with audio file to n8n webhook)
2. **n8n receives and processes**:
   - Converts audio format if needed
   - Calls Groq Whisper API for transcription
   - Calls Groq LLM to extract: name, description, urgency, priority, device, location
3. **n8n creates GLPI ticket**:
   - Authenticates to GLPI via REST API
   - Sends POST request to `/Ticket` endpoint
   - Receives ticket confirmation
4. **Logging and monitoring**:
   - n8n logs event to Loki
   - Promtail collects Docker container logs
   - Prometheus scrapes metrics from all services
5. **Visualization**:
   - Grafana displays metrics, dashboards, and logs
   - Users see tickets created, system health, error rates

## Technology Stack

- **Containers**: Docker, Docker Compose
- **ITSM**: GLPI 11+
- **Automation**: n8n (low-code workflow engine)
- **External APIs**: Groq (LLM + speech-to-text)
- **Monitoring**: Prometheus, Grafana
- **Logging**: Loki, Promtail
- **App Language**: Go (for sample TNS monitoring app)
- **Database**: MySQL

## Repository Structure

```
glpi-n8n-dashboard/
├── README.md                              # Main entry point
├── AGENTS.md                              # Documentation guidelines
├── .gitignore                             # Files excluded from git
├── .env.example                           # Template for environment variables
├── docs/                                  # Full documentation
│   ├── 00-project-overview.md            # This file
│   ├── 01-architecture.md                # System design diagrams
│   ├── 02-installation.md                # Setup guide
│   ├── 03-configuration.md               # Environment configuration
│   ├── 04-n8n-workflows.md               # Workflow documentation
│   ├── 05-glpi-integration.md            # GLPI API details
│   ├── 06-dashboard.md                   # Dashboard app documentation
│   ├── 07-monitoring-stack.md            # Prometheus/Grafana/Loki setup
│   ├── 08-docker-services.md             # Docker Compose details
│   ├── 09-troubleshooting.md             # Common issues
│   └── 10-security-and-secrets.md        # Secret management
├── infra/                                 # Infrastructure as code
│   ├── glpi-docker-compose.yml           # GLPI + MySQL
│   ├── tutorial-environment-docker-compose.yml  # Monitoring stack
│   ├── grafana/                          # Grafana provisioning
│   │   ├── dashboards/                   # Pre-built dashboards
│   │   └── provisioning/                 # Data source config
│   ├── prometheus/                       # Prometheus scrape config
│   └── promtail/                         # Promtail log scraper config
├── n8n/                                   # n8n workflows
│   ├── workflows/
│   │   ├── workflows.json                # Exported workflows
│   │   └── README.md                     # Workflow index
│   └── README.md
├── glpi/                                  # GLPI-specific documentation
│   └── README.md
├── dashboard/                             # Dashboard app
│   ├── app/                              # Go source code
│   │   ├── main.go
│   │   ├── Dockerfile
│   │   ├── go.mod
│   │   └── index.html.tmpl
│   ├── align-convertx/                   # Static HTML (unclear purpose)
│   └── README.md
└── scripts/                               # Utility scripts
    └── README.md
```

## Contact & Attribution

- **Original Developer**: BAKKALI (email from workflow export)
- **Grafana Workshop Materials**: app/ from Grafana Monitoring Workshop
- **GLPI**: https://glpi-project.org/
- **n8n**: https://n8n.io/
- **Groq**: https://groq.com/

## Next Steps

For local setup, begin with [02-installation.md](02-installation.md).
For detailed architecture, see [01-architecture.md](01-architecture.md).
