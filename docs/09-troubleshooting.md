# Troubleshooting

## Common Issues & Solutions

### Container Issues

#### "docker: command not found"

**Cause**: Docker not installed or not in PATH

**Solution**:
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Verify installation: `docker --version`
3. On Linux, may need to add user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

#### "Cannot connect to Docker daemon"

**Cause**: Docker Desktop not running

**Solution**:
1. Windows/macOS: Start Docker Desktop application
2. Linux: Start Docker service:
   ```bash
   sudo systemctl start docker
   ```

#### "Port is already allocated"

**Cause**: Another service using the port

**Solution**:
1. Find what's using port:
   ```bash
   # Windows
   netstat -ano | findstr :8080
   
   # macOS/Linux
   lsof -i :8080
   ```

2. Either stop that service or change port in docker-compose:
   ```yaml
   ports:
     - "8081:80"  # Use 8081 instead of 8080
   ```

3. Restart containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

#### "Out of memory"

**Cause**: Containers using too much RAM

**Solution**:
```bash
# Check container resource usage
docker stats

# Limit container memory
docker update --memory 512m glpi

# Or in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
```

### GLPI Issues

#### "GLPI not accessible at localhost:8080"

**Cause**: 
- Container not running
- Port mapping issue
- GLPI still initializing

**Solution**:
```bash
# Check if container is running
docker ps | grep glpi

# If not running, check logs
docker logs glpi

# Wait 30 seconds for initialization
sleep 30
curl http://localhost:8080

# If still failing, restart
docker-compose restart glpi
```

#### "Can't login to GLPI (incorrect password)"

**Cause**: Default credentials may have changed or not set properly

**Solution**:
1. Check what password is configured:
   ```bash
   grep GLPI_DB_PASSWORD infra/glpi-docker-compose.yml
   ```
   (Should be `glpi123`)

2. Try login with `glpi:glpi`

3. If password was changed, reset via direct database:
   ```bash
   docker-compose exec db mysql -u glpi -p"glpi123"
   use glpi;
   UPDATE glpi_users SET password = ENCRYPT('glpi') WHERE name = 'glpi';
   ```

#### "REST API not working (401 Unauthorized)"

**Cause**: API not enabled or credentials wrong

**Solution**:
1. Enable API in GLPI:
   - Go to Setup → Authentication → API
   - Check "Enable REST API"
   - Save

2. Verify credentials:
   ```bash
   # Test basic auth (should return session_token)
   curl -H "Authorization: Basic Z2xwaTpnbHBp" \
     http://localhost:8080/apirest.php/initSession
   ```

3. If fails, check GLPI logs:
   ```bash
   docker logs glpi
   ```

#### "GLPI can't connect to MySQL"

**Cause**: MySQL not running or connection parameters wrong

**Solution**:
```bash
# Check if MySQL container is running
docker ps | grep mysql

# Check MySQL logs
docker logs glpi-db-1

# Verify MySQL is ready
docker-compose exec db mysql -u glpi -p"glpi123" -e "SELECT 1"

# Restart both containers
docker-compose down
docker-compose up -d
```

### n8n Issues

#### "n8n not accessible at localhost:5678"

**Cause**: Container not running or port in use

**Solution**:
```bash
# Check if running
docker ps | grep n8n

# Check logs
docker logs tutorial-environment_n8n_1

# Restart
docker-compose -f infra/tutorial-environment-docker-compose.yml restart n8n
```

#### "n8n can't reach GLPI (connection refused)"

**Cause**: Docker networking issue or GLPI endpoint wrong

**Solution**:
1. Verify GLPI is running:
   ```bash
   docker-compose -f infra/glpi-docker-compose.yml ps
   ```

2. From n8n container, test connectivity:
   ```bash
   docker-compose exec n8n curl http://host.docker.internal:8080/apirest.php/initSession
   ```

3. If using Linux, replace `host.docker.internal` with GLPI container IP:
   ```bash
   docker inspect glpi | grep "IPAddress"
   ```

4. Update n8n workflow URL if needed

#### "Workflow fails with 'Groq API error'"

**Cause**: Invalid API key, quota exceeded, or network error

**Solution**:
1. Verify Groq API key in .env:
   ```bash
   echo $GROQ_API_KEY
   ```

2. Test key directly:
   ```bash
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   ```

3. Check if API quota is exceeded (look for rate limit errors)

4. Check n8n logs for detailed error:
   ```bash
   docker logs tutorial-environment_n8n_1 | grep error
   ```

#### "Workflow fails with 'LLM not returning valid JSON'"

**Cause**: LLM hallucinating or transcription too garbled

**Solution**:
1. Check transcribed text in workflow execution
2. Adjust prompt in AI BAKKALI node to be more specific
3. Add validation code node to handle malformed JSON
4. Test with clear audio

### Monitoring Stack Issues

#### "Prometheus not scraping metrics"

**Cause**: Target endpoint down, network issue, or misconfigured

**Solution**:
1. Check Prometheus targets: http://localhost:9090/targets
2. If "DOWN":
   - Verify endpoint is running: `docker ps`
   - Test connectivity from Prometheus container:
     ```bash
     docker-compose exec prometheus curl http://app:80/metrics
     ```
   - Check firewall rules

#### "Loki not receiving logs"

**Cause**: Promtail not pushing or Loki not receiving

**Solution**:
```bash
# Check Promtail logs
docker logs tutorial-environment_promtail_1

# Verify Loki is healthy
curl http://localhost:3100/loki/api/v1/push

# Check if container logs exist
docker inspect app | grep "LogPath"
```

#### "Grafana can't connect to data sources"

**Cause**: Network issue or data source misconfigured

**Solution**:
1. Go to Grafana → Configuration → Data Sources
2. Test connection (click "Save & Test")
3. If fails, check from Grafana container:
   ```bash
   docker-compose exec grafana curl http://prometheus:9090
   docker-compose exec grafana curl http://loki:3100
   ```

#### "High memory usage from Loki/Prometheus"

**Cause**: Too much data or retention too long

**Solution**:
```bash
# Check memory usage
docker stats tutorial-environment_loki_1 tutorial-environment_prometheus_1

# Reduce Prometheus retention
docker-compose down
# Edit prometheus.yml or docker-compose.yml
# Set: --storage.tsdb.retention.size=1GB

# Reduce Loki retention
# Edit loki config in docker-compose.yml:
# retention_period: 24h  # Instead of 7d

docker-compose up -d
```

### Network Issues

#### "Containers can't reach each other"

**Cause**: Network not created or routing broken

**Solution**:
```bash
# List networks
docker network ls

# Inspect network
docker network inspect glpi_default

# Check if all containers are connected
docker ps | grep glpi
docker inspect <container_id> | grep "Networks"

# Restart docker-compose
docker-compose down
docker-compose up -d
```

#### "Can't reach container from host (Windows/macOS)"

**Cause**: Docker Desktop networking limitation

**Solution**:
1. Use `localhost:<port>` (not container IP)
2. Use `host.docker.internal` from inside containers
3. Verify port mapping:
   ```bash
   docker port glpi
   ```

### Database Issues

#### "MySQL data lost after container restart"

**Cause**: No persistent volume or volume deleted

**Solution**:
1. Always use named volumes in docker-compose:
   ```yaml
   volumes:
     - db_data:/var/lib/mysql  # Not an anonymous volume
   ```

2. Never run `docker-compose down -v` unless you want to delete data

3. Backup important data:
   ```bash
   docker-compose exec db mysqldump -u glpi -p glpi > backup.sql
   ```

#### "MySQL won't start (permission denied)"

**Cause**: Volume permissions issue

**Solution**:
```bash
# Remove the problematic container
docker-compose rm db

# Recreate (Docker will reinitialize)
docker-compose up -d db
```

### Performance Issues

#### "Slow response times"

**Cause**: High CPU/memory usage or slow network

**Solution**:
1. Check resource usage:
   ```bash
   docker stats
   ```

2. Increase resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: "2"
         memory: 4G
   ```

3. Check for disk I/O:
   ```bash
   # macOS: activity monitor
   # Linux: iostat, iotop
   # Windows: Task Manager
   ```

4. Optimize queries in Prometheus/Loki

## Getting Help

### Enable Debug Logging

For deeper troubleshooting, enable debug logs:

```bash
# n8n debug
docker-compose -f infra/tutorial-environment-docker-compose.yml \
  exec n8n env DEBUG=* curl http://...

# GLPI debug
docker exec glpi tail -f /var/log/apache2/error.log
```

### Collect System Information

For bug reports:

```bash
# Docker version
docker --version
docker-compose --version

# Container status
docker-compose ps
docker-compose logs --tail=50

# System resources
docker stats --no-stream

# Mounted volumes
docker volume ls

# Network information
docker network ls
docker network inspect glpi_default
```

### Useful Commands Reference

```bash
# General
docker ps                                    # List running containers
docker ps -a                                 # List all containers
docker logs <container>                      # View container logs
docker exec -it <container> sh               # Enter container shell
docker-compose config                        # View composed config

# Troubleshooting
docker inspect <container>                   # Full container details
docker stats                                 # Live resource usage
docker network inspect <network>             # Network details
docker volume ls                             # List volumes
docker volume inspect <volume>               # Volume details

# Cleanup
docker system prune                          # Remove unused resources
docker container prune                       # Remove stopped containers
docker image prune                           # Remove unused images
```

---

See [02-installation.md](02-installation.md) for setup.
See [10-security-and-secrets.md](10-security-and-secrets.md) for security best practices.
