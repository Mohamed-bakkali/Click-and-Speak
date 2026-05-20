# n8n Workflows

## Overview

This folder contains n8n workflow definitions exported as JSON.

**File**: `workflows.json`

## Workflows Included

### 1. "My workflow"

Inactive (demo/reference)

**Purpose**: Basic audio → AI → GLPI ticket flow

**Flow**:
- Webhook receives audio file
- Convert to MP3
- Transcribe with Groq Whisper
- Extract details with Groq LLM
- Authenticate with GLPI
- Create ticket
- Optionally create Grafana dashboard

### 2. "Click & Speak ITSM" (Recommended)

Active

**Purpose**: Production workflow with enhanced error handling and Loki logging

**Flow**:
- Webhook receives audio file
- Detailed error checking for missing audio
- Convert to MP3
- Transcribe with Groq Whisper
- Extract details with Groq LLM
- Authenticate with GLPI
- Create ticket
- Format and send log to Loki
- Provides comprehensive audit trail

## Importing Workflows

### Into n8n

1. Open http://localhost:5678
2. Go to **Workflows** → **Import from File**
3. Select `workflows.json`
4. Both workflows will be imported

### Exporting Workflows

To export your modified workflows:

1. In n8n: Workflow → Menu → Export
2. Save as `.json` file
3. Replace `workflows.json` in this folder
4. Commit to git (credentials are not exported)

**Note**: n8n automatically excludes credentials from exports for security.

## Configuration Before Running

### 1. Groq API Credentials

Before activating workflows, you must configure Groq API access:

1. In n8n: **Settings** → **Credentials**
2. Create new credential:
   - Type: `HTTP Custom Auth` or `Groq API`
   - Add header: `Authorization: Bearer <your_groq_api_key>`
   - Name it `groq-api`
3. Update workflow nodes to reference this credential

### 2. GLPI Credentials

**Current**: Hardcoded as demo (`glpi:glpi`)

**For production**, use n8n Credentials:

1. Create HTTP Custom Auth credential with GLPI URL and auth
2. Update workflow nodes to use this credential

### 3. Test Workflow

1. Open "Click & Speak ITSM" workflow
2. Click **Test** (button in top-right)
3. Manually trigger webhook (or upload sample audio)
4. Watch execution history for results

## Webhook URL

Once activated, the webhook URL is:

```
http://localhost:5678/webhook/nouveau-ticket
```

For external access, get from n8n UI (Workflow → Details → Webhook URL).

## Expected Input

### Request Format

```
POST /webhook/nouveau-ticket
Content-Type: multipart/form-data

audio: <binary audio file>
name: (optional) User name
description: (optional) Brief description
```

### Success Response

```json
{
  "ticketId": 12345,
  "status": "created",
  "message": "Ticket created successfully"
}
```

### Error Response

```json
{
  "error": "No audio file provided",
  "message": "Description of what went wrong"
}
```

## Monitoring & Debugging

### View Execution History

1. Open workflow in n8n
2. Go to **Executions** tab
3. Click on any execution to see:
   - Input data
   - Output from each node
   - Error messages

### Enable Debug Mode

In n8n:

1. Settings → **Feature Flags**
2. Enable `Show node parameters in function`
3. Add console.log statements in Code nodes

### Check Logs

```bash
# n8n container logs
docker logs tutorial-environment_n8n_1 -f

# Filter for errors
docker logs tutorial-environment_n8n_1 | grep -i error
```

## Customization

### Modify AI Extraction Prompt

Edit the **AI BAKKALI** node:

1. Open workflow
2. Click on **AI BAKKALI** node
3. Modify the prompt field to change extraction logic
4. Example: add field for phone number, department, etc.

### Add New Workflow Step

1. Click **+** button to add node
2. Select node type
3. Configure and connect

### Add Notification

After ticket creation, send notification:

1. Add Email or Slack node
2. Configure with credentials
3. Connect to **TICKETS GLBI** node output
4. Send ticket details in message

## Known Limitations

- Audio must be clear and understandable
- LLM extraction relies on speech quality
- Groq API has rate limits (check quota)
- No persistent storage of workflow state across n8n restarts
- Credentials are stored in n8n only (not in JSON export)

## Troubleshooting

### Workflow Fails at Whisper

**Cause**: Audio file corrupted or unsupported format

**Solution**:
- Ensure audio is MP3, WAV, or similar format
- Check file size (Groq limit is 25MB)
- Test with sample audio file

### Workflow Fails at AI Extraction

**Cause**: LLM returning non-JSON or malformed JSON

**Solution**:
- Check transcription is readable
- Add input validation code node
- Increase prompt clarity

### Workflow Fails at GLPI

**Cause**: GLPI endpoint unreachable or credentials wrong

**Solution**:
- Verify GLPI is running: `docker ps | grep glpi`
- Test endpoint: `curl http://localhost:8080/apirest.php/initSession`
- Check GLPI API is enabled in Setup → Authentication

### Loki Logging Fails

**Cause**: Loki endpoint unreachable

**Solution**:
- Verify Loki is running: `docker ps | grep loki`
- Check endpoint: `curl http://localhost:3100/ready`
- Verify URL in workflow (should be `http://host.docker.internal:3100` from n8n)

## Performance Tips

- Use Whisper (faster) instead of other speech-to-text APIs
- Cache GLPI session tokens when possible
- Batch logs to Loki instead of sending individually
- Monitor n8n memory usage with `docker stats`

---

See [docs/04-n8n-workflows.md](../docs/04-n8n-workflows.md) for detailed documentation.
See [docs/02-installation.md](../docs/02-installation.md) for setup.
