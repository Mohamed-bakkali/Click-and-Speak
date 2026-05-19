# GLPI Integration

## GLPI Overview

GLPI (Gestionnaire Libre de Parc Informatique) is an open-source IT asset management and ticketing system. In this project, it serves as the backend for storing and managing IT support tickets created by n8n workflows.

**Role in Project**:
- Central ticketing system
- Asset inventory tracking
- Ticket lifecycle management
- REST API for external integrations

## Docker Setup

GLPI runs in Docker via `infra/glpi-docker-compose.yml`.

### Services

```yaml
services:
  glpi:
    image: glpi/glpi:latest
    ports:
      - "8080:80"              # HTTP only (port 80 inside container → 8080 on host)
    volumes:
      - glpi_data:/var/glpi    # Persistent GLPI config and data
    environment:
      GLPI_DB_HOST: db         # MySQL service name (Docker internal)
      GLPI_DB_NAME: glpi       # Database name
      GLPI_DB_USER: glpi       # MySQL username
      GLPI_DB_PASSWORD: glpi123 # MySQL password (CHANGE IN PRODUCTION)
    depends_on:
      - db

  db:
    image: mysql:8.0
    volumes:
      - db_data:/var/lib/mysql # Persistent MySQL data
    environment:
      MYSQL_RANDOM_ROOT_PASSWORD: "yes"
      MYSQL_DATABASE: glpi
      MYSQL_USER: glpi
      MYSQL_PASSWORD: glpi123
```

### Starting GLPI

```bash
docker-compose -f infra/glpi-docker-compose.yml up -d
```

GLPI initializes on first start (~20-30 seconds). Check logs:

```bash
docker-compose -f infra/glpi-docker-compose.yml logs -f glpi
```

## Initial Configuration

### 1. Access GLPI Web Interface

http://localhost:8080

First login:
- Username: `glpi`
- Password: `glpi`

### 2. Enable REST API

1. Go to **Setup** → **Authentication** → **API**
2. Check **Enable REST API**
3. Save

### 3. Create API Client (App Token)

For programmatic access (n8n):

1. Go to **Setup** → **Authentication** → **API Clients**
2. Click **+Add API Client**
3. Fill in:
   - **Name**: `n8n-integration`
   - **Active**: ✓
4. Save
5. **Copy the App-Token** (displayed once)
6. Store in `.env` or n8n Credentials Store

### 4. Create Standard User Account (Optional)

For demo, workflow uses `glpi:glpi` credentials. For production:

1. Go to **Administration** → **Users**
2. Create new user (e.g., `n8n_api_user`)
3. Set secure password
4. Set minimal permissions (can create tickets only)
5. Use in n8n workflow instead of admin account

## REST API Endpoints

### GLPI Dashboard Overview

See [glpi-dashboard-overview.png](screenshots/glpi-dashboard-overview.png) for the main dashboard showing:
- **82 Tickets** — Total tickets in system
- **Ticket Status Breakdown**:
  - 57 Incoming (not yet assigned)
  - 2 Assigned
  - 18 Resolved
  - 5 Closed
  - 0 Delayed
  - 0 Recurring
- **Charts**:
  - Evolution of tickets over time (trend line)
  - Ticket status distribution by month (stacked bar)
  - Top categories and sources

See [glpi-ticket-detail.png](screenshots/glpi-ticket-detail.png) for a sample ticket showing:
- Ticket metadata (date, type, category, urgency, priority)
- Full description and status workflow
- Comments and history
- Attached assets and related items

### Authentication

All API requests require one of:

**Option 1: Basic Auth (Simple, Demo Only)**
```
Authorization: Basic base64(username:password)
```

Example: `Authorization: Basic Z2xwaTpnbHBp` = `glpi:glpi` base64 encoded

**Option 2: Session Token (Recommended)**

1. POST to `/apirest.php/initSession` with Basic Auth
2. Get `session_token` from response
3. Use token in subsequent requests:
   ```
   Session-Token: <token>
   ```

**Option 3: App Token**
```
Authorization: Bearer <app_token>
```

### Common Endpoints

#### Start Session

```
POST /apirest.php/initSession
Headers: Authorization: Basic <credentials>
Response: { "session_token": "...", "sessionId": 1 }
```

#### Create Ticket

```
POST /apirest.php/Ticket
Headers: Session-Token: <token>
Body:
{
  "input": {
    "name": "Ticket Title",
    "content": "Problem description",
    "urgency": 3,
    "priority": 3,
    "type": 1
  }
}
Response: { "id": 123, "name": "Ticket Title", "message": "Ticket created" }
```

**Field Mappings**:
- `urgency`: 1=Low, 2=Medium, 3=High, 4=Very High
- `priority`: 1=Low, 2=Medium, 3=High, 4=Very High
- `type`: 1=Request, 2=Incident, etc.

#### Get Ticket

```
GET /apirest.php/Ticket/123
Headers: Session-Token: <token>
Response: { "id": 123, "name": "...", "status": 2, ... }
```

#### Update Ticket

```
PUT /apirest.php/Ticket/123
Headers: Session-Token: <token>
Body:
{
  "input": {
    "status": 5
  }
}
```

#### List Tickets

```
GET /apirest.php/Ticket?range=0-100
Headers: Session-Token: <token>
Response: [ { "id": 1, "name": "...", ... }, ... ]
```

#### Logout Session

```
GET /apirest.php/killSession
Headers: Session-Token: <token>
Response: { "message": "Session deleted" }
```

## GLPI Configuration for n8n

### Step 1: Enable API (Already Covered)

### Step 2: Configure in n8n

n8n workflow is pre-configured with hardcoded credentials:

```
Authorization: Basic Z2xwaTpnbHBp  # = "glpi:glpi"
URL: http://host.docker.internal:8080/apirest.php/...
```

To use environment variables instead (production):

1. Store credentials in n8n Credentials Store:
   - Settings → **Credentials**
   - New credential: **HTTP Custom Auth**
   - Add your GLPI credentials
   - Name it `glpi-api`

2. Update workflow nodes to reference credentials:
   - Instead of hardcoded header: Use `Credentials: glpi-api`

### Step 3: Verify Connection

In n8n, add a test node:

```
n8n Expression: {{ $('AUTH & LOGIN GLBI').item.json.session_token }}
```

If it returns a token, connection is working.

## Ticket Lifecycle

### Status Codes

| Status | Code | Meaning |
|--------|------|---------|
| New | 1 | Newly created ticket |
| Assigned | 2 | Assigned to technician |
| Planned | 3 | Work scheduled |
| Waiting | 4 | Waiting for external action |
| Solved | 5 | Issue resolved |
| Closed | 6 | Ticket closed |

### Creating Tickets via n8n

Workflow automatically creates tickets with:
- Title: User name from AI extraction
- Description: Problem + device + location
- Urgency/Priority: Set to 3 (high)
- Type: 1 (request)
- No assignment (manual assignment needed)

### Automatic Assignment (Future)

To auto-assign tickets by category:

1. Create a second n8n workflow trigger
2. Listen for GLPI ticket creation webhook
3. Based on category/keywords, assign to appropriate technician
4. Send notification email

## GLPI Data Model

### Tickets Table

| Column | Type | Example |
|--------|------|---------|
| `id` | int | 12345 |
| `name` | varchar | "Printer not working" |
| `content` | text | "Printer on floor 3 offline" |
| `urgency` | int | 3 |
| `priority` | int | 3 |
| `status` | int | 1 (new) |
| `created_at` | timestamp | 2026-05-18 10:30:00 |
| `updated_at` | timestamp | 2026-05-18 10:30:00 |

### Assets Table

GLPI tracks IT assets (computers, printers, network devices, etc.). In this project, manually added via GLPI UI.

## Troubleshooting GLPI Integration

### "Unable to connect to GLPI"

**Cause**: n8n cannot reach GLPI container

**Solution**:
```bash
# From n8n container, test connectivity
docker-compose exec n8n curl http://glpi:80/apirest.php/initSession -v

# If fails, check network
docker network ls
docker network inspect glpi_default
```

### "401 Unauthorized"

**Cause**: Invalid credentials

**Solution**:
1. Verify Basic Auth header: `echo -n "glpi:glpi" | base64`
2. Try via browser: http://localhost:8080 (should login with glpi:glpi)
3. If browser works but API doesn't, check if API is enabled

### "GLPI_DB_HOST: Unknown host 'db'"

**Cause**: GLPI container can't reach MySQL (network issue)

**Solution**:
```bash
# Restart both containers
docker-compose down
docker-compose up -d

# Verify they're on same network
docker-compose ps
```

### "Session token expired"

**Cause**: Session token only valid for ~24 hours by default

**Solution**: Workflow calls `/initSession` each time, so it should generate fresh token. If still failing:
1. Check GLPI logs: `docker logs glpi`
2. Increase session timeout in GLPI Setup → System → Session

## API Rate Limiting

GLPI has no built-in rate limiting by default. To prevent overload:

- n8n workflow waits 1 second between API calls
- Implement application-level throttling if needed
- Monitor GLPI server load

## Backup & Restore

### Backup GLPI Data

```bash
# Backup database
docker-compose exec db mysqldump -u glpi -p glpi > glpi_backup.sql

# Backup file storage
docker cp glpi:/var/glpi ./glpi_backup
```

### Restore GLPI Data

```bash
# Restore database
docker-compose exec -T db mysql -u glpi -p glpi < glpi_backup.sql

# Restore files
docker cp glpi_backup glpi:/var/glpi
```

## Production Deployment

### Recommended Changes

1. **Use HTTPS**:
   - Add reverse proxy (nginx/Traefik)
   - Configure SSL certificate
   - Redirect HTTP → HTTPS

2. **Strong Authentication**:
   - Disable default `glpi:glpi` account
   - Create dedicated API user with minimal permissions
   - Use API tokens instead of passwords

3. **Database Security**:
   - Change MySQL root and glpi passwords
   - Store passwords in secrets vault (not .env)
   - Enable SSL for MySQL connections

4. **API Key Rotation**:
   - Rotate GLPI API tokens monthly
   - Log all API access
   - Monitor unusual patterns

5. **Monitoring & Alerting**:
   - Set up alerts for GLPI service downtime
   - Monitor MySQL disk space
   - Track API error rates

---

See [02-installation.md](02-installation.md) for setup.
See [09-troubleshooting.md](09-troubleshooting.md) for common issues.
