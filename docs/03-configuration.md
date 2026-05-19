# Configuration

## Environment Variables

All configuration is managed via `.env` file (local only, not committed to git).

### Creating .env

1. Copy the example:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   # .env (example)
   GROQ_API_KEY=gsk_your_key_here
   GLPI_DB_PASSWORD=your_secure_db_password
   GRAFANA_ADMIN_PASSWORD=your_grafana_password
   N8N_ENCRYPTION_KEY=your_encryption_key
   ```

### Variables Reference

#### GROQ API

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | ✓ Yes | None | Groq API key for Whisper speech-to-text and LLM |

**How to get**:
1. Go to https://console.groq.com/
2. Sign up or log in
3. Go to API Keys section
4. Create new key
5. Copy and paste into `.env`

#### GLPI Database

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GLPI_DB_HOST` | No | `db` | MySQL hostname (internal to Docker network) |
| `GLPI_DB_NAME` | No | `glpi` | Database name |
| `GLPI_DB_USER` | No | `glpi` | MySQL user |
| `GLPI_DB_PASSWORD` | No | `glpi123` | MySQL password — **Change in production** |

Currently hardcoded in `infra/glpi-docker-compose.yml`. To use environment variables:

```yaml
environment:
  MYSQL_PASSWORD: ${GLPI_DB_PASSWORD}
```

#### GLPI Service

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GLPI_HOST` | No | `localhost` | GLPI hostname (for external access) |
| `GLPI_PORT` | No | `8080` | GLPI port mapping (host side) |
| `GLPI_INTERNAL_PORT` | No | `80` | GLPI port inside container |

#### n8n Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `N8N_PORT` | No | `5678` | n8n web interface port |
| `N8N_ENCRYPTION_KEY` | No | Auto-generated | Encryption key for credentials (persist across restarts) |
| `N8N_DB_TYPE` | No | `sqlite` | Database backend (`sqlite` for dev, `postgres` for prod) |

To persist n8n data across container restarts, set a consistent encryption key:

```bash
N8N_ENCRYPTION_KEY=your_32_character_random_string_here
```

#### Grafana Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GF_SECURITY_ADMIN_PASSWORD` | No | `admin` | Grafana admin password |
| `GF_AUTH_ANONYMOUS_ORG_ROLE` | No | `Admin` | Allow anonymous access as admin (dev only) |
| `GF_AUTH_ANONYMOUS_ENABLED` | No | `true` | Enable anonymous access (dev only) |

**Security Note**: For production, disable anonymous access and use proper authentication.

#### Prometheus Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `PROMETHEUS_RETENTION` | No | `30d` | How long to keep metrics |

#### Loki Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LOKI_RETENTION_DAYS` | No | `7` | How long to keep logs (ephemeral by default) |

To enable persistent Loki storage:

```yaml
# In docker-compose.yml
volumes:
  - loki_data:/loki  # Add this
```

### .env.example Template

See `.env.example` in repository root.

### Using Environment Variables in Docker Compose

Example from `glpi-docker-compose.yml`:

```yaml
environment:
  GLPI_DB_PASSWORD: ${GLPI_DB_PASSWORD:-glpi123}
```

The `${VAR_NAME:-default}` syntax means:
- Use `VAR_NAME` from `.env` if set
- Otherwise use `default` value

To require a variable (fail if not set):

```yaml
environment:
  GROQ_API_KEY: ${GROQ_API_KEY}  # Will error if not in .env
```

### Environment Variables in n8n Workflows

n8n supports environment variable substitution in workflows:

**In workflow JSON**:
```json
{
  "url": "https://api.groq.com/openai/v1/...",
  "authentication": "genericCredentialType",
  "parameters": {
    "value": "={{ $vars.GROQ_API_KEY }}"
  }
}
```

**Better approach**: Use n8n Credentials instead of hardcoding in workflow.

### Rotating Secrets

1. **Groq API Key**:
   - Generate new key in Groq console
   - Update `GROQ_API_KEY` in `.env`
   - Restart n8n: `docker restart tutorial-environment_n8n_1`

2. **GLPI Database Password**:
   - Update `.env`
   - Recreate GLPI container: `docker-compose down && docker-compose up -d` (loses data if no volume backup)
   - Or use MySQL CLI to change password while running

3. **n8n Encryption Key**:
   - Stop n8n
   - Export credentials: Go to Settings → Export Credentials
   - Change `N8N_ENCRYPTION_KEY` in `.env`
   - Start n8n
   - Import credentials back

## Docker Compose Overrides

For local customization without editing tracked files, use `docker-compose.override.yml`:

```bash
# Create override file
cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  glpi:
    ports:
      - "8081:80"  # Use 8081 instead of 8080
  grafana:
    environment:
      GF_SECURITY_ADMIN_PASSWORD: my_custom_password
EOF
```

Docker Compose automatically applies overrides.

## Configuration for Different Environments

### Development (Current Setup)

- Credentials in `.env` (local only)
- Anonymous Grafana access enabled
- SQLite for n8n (single-file storage)
- No persistent volumes for logs
- Container restart automatically

### Production Deployment

**Recommended changes**:

1. **Secrets Management**:
   ```yaml
   secrets:
     groq_api_key:
       external: true  # Use Kubernetes/Docker Swarm secrets
     glpi_db_password:
       external: true
   ```

2. **Database**:
   ```yaml
   environment:
     N8N_DB_TYPE: postgres
     N8N_DB_HOST: postgres-db
     N8N_DB_NAME: n8n
   ```

3. **Persistent Storage**:
   ```yaml
   volumes:
     - glpi_data:/var/glpi
     - loki_data:/loki
   ```

4. **Ingress & TLS**:
   - Use reverse proxy (nginx, Traefik)
   - Enable HTTPS with Let's Encrypt
   - Add authentication middleware

5. **Monitoring**:
   - Add alerting rules
   - Configure log retention
   - Set up backup jobs

## Validation

To verify configuration is working:

```bash
# Check that environment variables are loaded
docker-compose config | grep -A5 "environment:"

# Check n8n can reach GLPI
docker-compose exec n8n curl http://glpi:80

# Check Prometheus scrape targets
curl http://localhost:9090/api/v1/targets | jq .
```

---

See [03-configuration.md](03-configuration.md) for security best practices.
