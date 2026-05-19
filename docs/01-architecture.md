# Architecture

## High-Level System Design

```mermaid
sequenceDiagram
    participant Input as 🎙️ Audio<br/>Input
    participant n8n
    participant Groq as Groq<br/>Cloud
    participant GLPI
    participant MySQL
    participant Loki
    participant Prom as Prometheus
    participant Grafana

    Input->>n8n: 1. Audio webhook
    n8n->>n8n: 2. Normalize audio
    n8n->>Groq: 3. Transcribe & extract
    Groq-->>n8n: 4. Text + JSON
    n8n->>GLPI: 5. Create ticket
    GLPI->>MySQL: 6. Store ticket
    MySQL-->>GLPI: 7. Confirm
    GLPI-->>n8n: 8. Ticket ID
    n8n->>Loki: 9. Log event
    Loki-->>n8n: 10. OK
    par Monitoring
        Prom->>n8n: 11a. Scrape metrics
        Prom->>GLPI: 11b. Scrape metrics
    and
        Prom->>Grafana: 12. Query metrics
        Loki->>Grafana: 13. Query logs
    end
```

This diagram shows the complete system flow from audio input through automation, external APIs, data storage, and parallel monitoring—all participants in the architecture and how they interact.

## Workflow Sequence

```mermaid
sequenceDiagram
    participant Client as User/<br/>Client
    participant n8n
    participant Audio as Audio<br/>Processing
    participant Groq
    participant GLPI
    participant Loki

    Client->>n8n: POST /nouveau-ticket<br/>(audio file)
    n8n->>Audio: Normalize<br/>(.webm → .mp3)
    Audio-->>n8n: MP3 stream
    n8n->>Groq: POST speech data<br/>(Whisper API)
    Groq-->>n8n: Transcript text
    n8n->>Groq: POST transcript<br/>(LLM extraction)
    Groq-->>n8n: Structured JSON<br/>(title, description, etc.)
    n8n->>GLPI: POST /initSession<br/>(auth)
    GLPI-->>n8n: Session token
    n8n->>GLPI: POST /Ticket<br/>(create ticket)
    GLPI-->>n8n: ticket_id, status
    n8n->>Loki: POST event<br/>(ticket created)
    Loki-->>n8n: 204 OK
    n8n-->>Client: Success response
```

This sequence shows the complete workflow: audio reception, normalization, AI transcription and extraction, GLPI authentication and ticket creation, and event logging.

## Container Networking

```mermaid
sequenceDiagram
    participant Client as External<br/>Client
    participant n8n
    participant GLPI
    participant MySQL as MySQL<br/>Database
    participant Groq as Groq<br/>Cloud API
    participant Prom as Prometheus
    participant Grafana
    participant Loki

    Client->>n8n: 1. POST /nouveau-ticket<br/>(Docker port 5678)
    n8n->>GLPI: 2. REST API calls<br/>(Docker network)
    GLPI->>MySQL: 3. Read/Write<br/>(internal container)
    n8n->>Groq: 4. HTTPS to cloud<br/>(external internet)
    Groq-->>n8n: 5. API response
    n8n->>Loki: 6. Push logs<br/>(Docker network)
    Prom->>n8n: 7. Scrape metrics<br/>(:5678/metrics)
    Prom->>Groq: 8. Scrape metrics<br/>(via proxy)
    Loki-->>Grafana: 9. Log streams
    Prom-->>Grafana: 10. Metrics queries
    Grafana-->>Client: 11. Dashboard<br/>(Docker port 3000)
```

This sequence depicts the network communication flow: client connections to exposed ports (5678, 3000), inter-container traffic over Docker network, and external API calls to Groq.

## GLPI Integration Sequence

```mermaid
sequenceDiagram
    participant User
    participant n8n
    participant Groq
    participant GLPI
    participant MySQL
    participant Loki

    User->>n8n: POST /nouveau-ticket
    n8n->>Groq: POST speech data
    Groq-->>n8n: text output
    n8n->>Groq: POST extracted ticket fields
    Groq-->>n8n: structured JSON
    n8n->>GLPI: POST /initSession
    GLPI-->>n8n: session_token
    n8n->>GLPI: POST /Ticket
    GLPI->>MySQL: INSERT ticket record
    GLPI-->>n8n: ticket_id
    n8n->>Loki: POST /loki/api/v1/push
    Loki-->>n8n: 204 No Content
```

This sequence diagram highlights the message flow between n8n, Groq, GLPI, and Loki during ticket creation.

## Monitoring Data Flow

```mermaid
sequenceDiagram
    participant n8n as n8n<br/>Metrics
    participant App as Dashboard<br/>App
    participant Logs as Container<br/>Logs
    participant Prom as Prometheus
    participant Promtail
    participant Loki
    participant Grafana as Grafana<br/>Dashboards

    n8n->>Prom: 1. Expose /metrics
    App->>Prom: 2. Expose /metrics
    Logs->>Promtail: 3. Stream logs
    Prom->>Prom: 4. Scrape all metrics<br/>(15s interval)
    Promtail->>Loki: 5. Push logs batch
    Prom->>Grafana: 6. Query metrics
    Loki->>Grafana: 7. Query logs
    Grafana-->>Grafana: 8. Render dashboards
```

This sequence illustrates the observability pipeline: metrics scraped by Prometheus, logs shipped by Promtail to Loki, and both data sources queried by Grafana for visualization.

## Error Handling & Fallbacks

### Current State
- n8n has `maxTries: 5` on GLPI requests (retry on fail)
- `alwaysOutputData: true` on critical nodes (continue even if previous step fails)
- Error logs posted to Loki for visibility

### Recommended Improvements
- [ ] Add error notification webhook
- [ ] Implement dead-letter queue for failed tickets
- [ ] Add circuit breaker for Groq API failures
- [ ] Implement exponential backoff for transient failures
- [ ] Create alerting rules in Grafana for workflow failures

---

See [02-installation.md](02-installation.md) for how to stand up this architecture locally.
