# GLPI

GLPI is an open-source IT asset management and ticketing system. In this project, it serves as the backend for IT support tickets created automatically by n8n workflows.

## Running GLPI

GLPI runs entirely in Docker. No local installation needed.

**Start GLPI**:

```bash
docker-compose -f ../infra/glpi-docker-compose.yml up -d
```

**Access**:

- URL: http://localhost:8080
- Username: `glpi`
- Password: `glpi`

**Stop GLPI**:

```bash
docker-compose -f ../infra/glpi-docker-compose.yml down
```

## Initial Setup

1. **Enable REST API**:
   - Log in as `glpi`
   - Go to Setup → Authentication → API
   - Check "Enable REST API"
   - Save

2. **Create API Client** (for n8n integration):
   - Setup → Authentication → API Clients
   - Create new client named `n8n-integration`
   - Copy the App-Token
   - Store in `.env` or n8n Credentials Store

## Integration with n8n

n8n workflows automatically create GLPI tickets via REST API:

```
POST /apirest.php/Ticket
Headers: Session-Token: <token>
Body: { name, content, urgency, priority, type }
```

See [../docs/05-glpi-integration.md](../docs/05-glpi-integration.md) for API details.

## Data Persistence

- **Config & Plugins**: Stored in Docker volume `glpi_data`
- **Database**: MySQL container with volume `db_data`

Both volumes persist across container restarts.

**Backup**:

```bash
docker-compose exec db mysqldump -u glpi -p glpi > backup.sql
```

## Troubleshooting

**Can't log in**: Try default `glpi:glpi` or check docker logs

```bash
docker logs glpi
```

**Can't reach at localhost:8080**: Check if container is running

```bash
docker-compose ps
```

**API returns 401**: Check if API is enabled and credentials are correct

See [../docs/09-troubleshooting.md](../docs/09-troubleshooting.md) for more issues.

## Next Steps

- [../docs/02-installation.md](../docs/02-installation.md) — Full setup guide
- [../docs/05-glpi-integration.md](../docs/05-glpi-integration.md) — API integration details
- [../docs/04-n8n-workflows.md](../docs/04-n8n-workflows.md) — Workflow automation

