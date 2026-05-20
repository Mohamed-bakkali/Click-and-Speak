# Security & Secrets Management

## Files & Credentials That Should Not Be Committed

The following files and credentials are configured in `.gitignore` to prevent accidental commits:

1. **.env** (local configuration with real values)
2. **n8n credential exports** (contain encrypted API keys)
3. **GLPI tokens** (App-Token, User-Token, session tokens)
4. **Groq API keys** (enable speech-to-text and LLM)
5. **Database passwords** (MySQL root, GLPI user)
6. **SSH keys** (*.pem, *.key files)
7. **Docker inspect files** (_docker-inspect/, volume dumps)
8. **Scripts with exposed credentials** (scripts-groq-to-loki.py)
9. **Config files containing secrets** (docker-compose overrides with passwords)
10. **Browser cookies/sessions** (localStorage, sessionStorage from GLPI)

## Environment Variables & .env

### How .env Works

1. `.env` is a local configuration file (git-ignored)
2. Docker Compose automatically reads it
3. Values are injected as environment variables
4. Used in docker-compose.yml via `${VAR_NAME}` syntax

### Creating .env

**Copy the template**:

```bash
cp .env.example .env
```

**.env.example Contains**:

- Variable names
- Comments explaining each variable
- Safe example values (where applicable)
- NO real credentials

**.env Contains**:

- Your actual API keys (Groq)
- Your database passwords
- Your Grafana admin password
- Your n8n encryption key

### Protecting .env

```bash
# Make .env readable only by owner
chmod 600 .env

# Verify
ls -la .env  # Should show: -rw------- (or rw-_-_-_)
```

### Updating .env.example

When adding new configuration:

1. Add to `.env.example` with a placeholder or safe default
2. Document what it does in comments
3. Never add real values to `.env.example`
4. Commit `.env.example` to git

Example:

```bash
# Good
GROQ_API_KEY=gsk_your_key_here_replace_this

# Bad
GROQ_API_KEY=gsk_RXHFKu...[truncated_fake_key]
```

## API Keys & Credentials

### Groq API Key

Store your Groq API key in `.env`, never in `.env.example` or committed files. The key is used for speech-to-text transcription and LLM processing in n8n workflows.

Get a key from https://console.groq.com/:
1. Sign up or log in
2. Go to API Keys section
3. Create new key
4. Paste into `.env`

### GLPI Credentials

**Default credentials (demo only)**:

```
Username: glpi
Password: glpi
```

**For production**:

1. Change GLPI admin password:
   - GLPI UI → Administration → Users → glpi
   - Set new password (20+ characters, mixed)

2. Create dedicated API user:
   - Username: `n8n_api`
   - Password: Auto-generated, 32+ character
   - Permissions: Create tickets only
   - Store in n8n Credentials Store

3. Disable default admin account (optional):
   - GLPI UI → Administration → Users → glpi
   - Set to inactive

### n8n Credentials Storage

n8n encrypts credentials using the encryption key:

```
N8N_ENCRYPTION_KEY=<random_32_char_string>
```

**Storing credentials in n8n**:

1. Settings → Credentials
2. Add new credential
3. n8n encrypts it automatically
4. Never exposed in plaintext in workflow JSON
5. Persists across restarts (if encryption key stays same)

**Exporting workflows safely**:

- n8n exports workflows WITHOUT embedded credentials
- You need to manually re-enter credentials after import
- This prevents accidental credential leaks

### Database Passwords

**MySQL in docker-compose**:

```yaml
environment:
  MYSQL_PASSWORD: ${GLPI_DB_PASSWORD}  # From .env
  MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}  # From .env
```

**Files that should not be committed to git:**
- Real passwords in docker-compose.yml
- Database dumps with passwords
- MySQL connection strings with credentials

**Rotating password**:

1. Update `.env`
2. Stop containers: `docker-compose down`
3. Delete volume: `docker volume rm glpi_db_data`
4. Start fresh: `docker-compose up -d`

(This loses data—backup first if needed.)

## File Permissions

### GLPI Volumes

When mounted to Docker, files inherit permissions from host.

**Secure setup**:

```yaml
volumes:
  glpi_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /secure/path/glpi  # Owned by docker user
```

```bash
# Ensure directory is readable only by docker
sudo chown 999:999 /secure/path/glpi  # n8n UID:GID in container
sudo chmod 700 /secure/path/glpi
```

### n8n Data

```bash
# Restrict access
chmod 700 n8n_data  # Only owner can read/write
```

## Network Security

### Container Networking

By default, Docker Compose creates isolated networks:

```
n8n → can only reach other containers on same network
Containers → cannot reach host except via port mappings
```

**More secure setup** (separate networks):

```yaml
networks:
  internal:
    internal: true  # Cannot reach external internet
  external:
    # Can reach internet

services:
  glpi:
    networks:
      - internal

  n8n:
    networks:
      - internal
      - external  # Needs to reach Groq API
```

### Firewall Rules (Production)

Only expose needed ports:

```yaml
ports:
  - "8080:80"   # GLPI (for techs to create tickets)
```

Internal monitoring ports (Prometheus 9090, Loki 3100, n8n 5678) should not be exposed on the production firewall.

In production, use reverse proxy:

```
User → NGINX (port 80/443) → GLPI (port 8080)
```

### HTTPS/TLS

Current setup: HTTP only (dev safe, prod not safe).

**For production**:

1. Use Let's Encrypt (free SSL)
2. Configure reverse proxy (nginx):

```nginx
server {
  listen 443 ssl;
  ssl_certificate /etc/letsencrypt/live/domain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/domain.com/privkey.pem;
  location / {
    proxy_pass http://glpi:80;
  }
}
```

3. Redirect HTTP to HTTPS:

```nginx
server {
  listen 80;
  return 301 https://$server_name$request_uri;
}
```

## Accessing Services Safely

### From Host (Development)

Local access (`http://localhost:8080`) is isolated to your machine and is the standard development approach.

Network access (`http://<machine-ip>:8080`) exposes the service to other machines on the same network.

### From External Network (Production)

1. Use VPN or bastion host
2. Restrict IPs in firewall
3. Use authentication (OAuth, LDAP)
4. Enable 2FA on admin accounts

### Remote Access

For remote access, use a secure tunnel or VPN rather than directly exposing services to the internet.

**SSH tunnel approach**:
   ```bash
   ssh -L 8080:localhost:8080 user@remote-server
   # Access via localhost:8080
   ```

2. Use VPN (Wireguard, OpenVPN)

3. Use SSH bastion:
   ```bash
   ssh -J bastion.example.com glpi.internal.example.com
   ```

## Audit & Monitoring

### Logging Access

Enable access logs in GLPI:

- Setup → System → Log → Enable all
- Review logs in Administration → Logs

### Monitoring Secret Changes

Keep a changelog:

```bash
# When rotating API keys, document it
git log --oneline --all | grep -i "rotate\|update.*key"
```

### Regular Audits

1. **Monthly**: Review `.env` values, ensure keys are current
2. **Monthly**: Check GLPI user accounts (disable inactive)
3. **Quarterly**: Review Docker image versions (check for CVEs)
4. **Quarterly**: Rotate long-lived credentials

## Backup & Recovery

### Backup Strategy

```bash
# Backup everything
docker-compose exec db mysqldump -u glpi -p glpi > glpi_backup_$(date +%Y%m%d).sql
tar czf glpi_volumes_$(date +%Y%m%d).tar.gz -C /var/lib/docker/volumes/ .
```

### Restore from Backup

```bash
# Restore database
docker-compose exec -T db mysql -u glpi -p glpi < glpi_backup_20260518.sql

# Restore volumes
tar xzf glpi_volumes_20260518.tar.gz -C /var/lib/docker/volumes/
```

**Security note**: Backups contain database including hashes. Treat as sensitive.

## Compliance & Best Practices

### Compliance with OWASP Top 10

This project addresses several OWASP categories:

- **A02:2021 – Cryptographic Failures**: Uses encryption keys and can use TLS
- **A03:2021 – Injection**: Validate all inputs in LLM prompts
- **A07:2021 – Identification & Authentication**: GLPI login and API tokens
- **A09:2021 – Logging & Monitoring**: Loki and Prometheus integration

### GDPR / Data Protection

If processing personal data:

1. **Data Minimization**: Don't collect unnecessary data
2. **Retention**: Delete logs after 30 days (set retention)
3. **Encryption**: Use HTTPS in production
4. **Access Control**: Restrict who can view tickets
5. **Audit Trail**: Log all access to sensitive data

### PCI-DSS (if handling payment data)

This project stores data in plaintext in MySQL, transmits over HTTP by default, and has no encryption at rest. It is not suitable for payment data processing without significant additional security infrastructure.

## Incident Response

### If a key is leaked:

1. **Immediately**: Revoke the key in the service dashboard
2. **Within 1 hour**: Rotate to new key, update `.env`
3. **Within 24 hours**: Force-push git history (remove old commits)
4. **Within 48 hours**: Audit what was accessed with leaked key

### If database is breached:

1. **Immediately**: Take services offline
2. **Review**: Check backup dumps for passwords
3. **Reset**: Change all passwords
4. **Restore**: Use clean backup or rebuild from scratch
5. **Improve**: Add better access controls, encryption

## Security Checklist

Before deploying to production:

- [ ] No real secrets in `.env.example`
- [ ] `.env` is git-ignored
- [ ] All Docker images are up-to-date
- [ ] Database password is strong (20+ chars, mixed case)
- [ ] GLPI admin password is strong
- [ ] HTTPS/TLS is configured
- [ ] API rate limiting is enabled
- [ ] Firewall restricts port access
- [ ] Backup strategy is tested
- [ ] Audit logging is enabled
- [ ] Team is trained on secret handling
- [ ] Regular security audits are scheduled

---

See [02-installation.md](02-installation.md) for setup.
See [03-configuration.md](03-configuration.md) for .env configuration.
