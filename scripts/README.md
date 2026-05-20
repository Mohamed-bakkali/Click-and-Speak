# Scripts

Utility scripts for the project.

## Files

### groq_to_loki.py

**Purpose**: Monitor Groq API usage and push metrics to Loki.

Example/demo — uses environment variable for API key; see .env.example

**What it does**:
- Queries Groq API for list of available models
- Collects usage statistics
- Sends logs to Loki every 5 minutes
- Tracks API health and model availability

**Dependencies**:
- Python 3.6+
- `requests` library

**Setup**:

```bash
# Install dependencies
pip install requests

# Set API key (do not hardcode)
export GROQ_API_KEY="gsk_your_key_here"

# Run
python groq_to_loki.py
```

**Configuration**:

Edit script variables:

```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Use env var, not hardcoded
LOKI_URL = "http://localhost:3100/loki/api/v1/push"
INTERVAL_SECONDS = 300  # 5 minutes
```

**Running in Docker**:

```bash
docker run -e GROQ_API_KEY="$GROQ_API_KEY" \
  -v ./scripts:/scripts \
  python:3.9 \
  python /scripts/groq_to_loki.py
```

**Or in docker-compose**:

```yaml
services:
  groq_monitor:
    image: python:3.9
    volumes:
      - ./scripts:/scripts
    environment:
      GROQ_API_KEY: ${GROQ_API_KEY}
      LOKI_URL: http://loki:3100/loki/api/v1/push
    command: pip install requests && python /scripts/groq_to_loki.py
    depends_on:
      - loki
```

**Output**:

Sends logs to Loki with labels:

```json
{
  "stream": {
    "service": "groq-monitor",
    "job": "groq-api-stats"
  },
  "values": [
    ["timestamp", "log_message"]
  ]
}
```

**Troubleshooting**:

- API key invalid: Check Groq console
- Loki not reachable: Verify URL and Loki running
- High memory: Script may accumulate data, restart periodically

## Creating New Scripts

1. Create `.py`, `.sh`, or `.js` file in `scripts/`
2. Add to `.gitignore` if it contains credentials
3. Document in this README
4. Include error handling and logging
5. Use environment variables for configuration (not hardcoded values)

## Best Practices

- ✓ Use environment variables for secrets
- ✓ Log errors to Loki or monitoring system
- ✓ Add timeouts to external API calls
- ✓ Implement exponential backoff for retries
- ✗ Do not hardcode API keys
- ✗ Do not commit credentials
- ✗ Do NOT assume services are always reachable

---

See [../docs/10-security-and-secrets.md](../docs/10-security-and-secrets.md) for security guidelines.
