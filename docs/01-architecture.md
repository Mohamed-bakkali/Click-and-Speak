# Architecture

## High-Level System Design

```mermaid
graph TB
    subgraph input[" INPUT "]
        audio["🎙️ Audio Webhook<br/>POST /nouveau-ticket"]
    end

    subgraph core[" CORE AUTOMATION (n8n) "]
        w1["Receive<br/>Webhook"]
        w2["Normalize<br/>Audio"]
        w3["Whisper<br/>Transcribe"]
        w4["LLM<br/>Extract"]
        w5["Create<br/>Ticket"]
    end

    subgraph external[" EXTERNAL APIs "]
        groq["Groq<br/>Whisper + LLM"]
        glpi_svc["GLPI<br/>HTTP REST"]
    end

    subgraph backend[" DATA LAYER "]
        glpi_db["GLPI DB<br/>MySQL"]
        loki_logs["Loki<br/>Logs"]
    end

    subgraph observability[" MONITORING "]
        prom["Prometheus<br/>Metrics"]
        grafana_dash["Grafana<br/>Dashboards"]
    end

    audio --> w1 --> w2 --> w3 --> w4 --> w5
    w3 -.->|API| groq
    w4 -.->|API| groq
    w5 -.->|HTTP| glpi_svc
    glpi_svc --> glpi_db
    w5 --> loki_logs
    prom -.->|scrape| w1
    prom -.->|scrape| glpi_svc
    loki_logs -.->|stream| grafana_dash
    prom -.->|query| grafana_dash

    style input fill:#00BCD4,color:#000,stroke:#0097A7,stroke-width:3px
    style core fill:#66BB6A,color:#000,stroke:#2E7D32,stroke-width:3px
    style external fill:#FFB74D,color:#000,stroke:#F57C00,stroke-width:3px
    style backend fill:#AB47BC,color:#fff,stroke:#6A1B9A,stroke-width:3px
    style observability fill:#42A5F5,color:#000,stroke:#1565C0,stroke-width:3px
    style w1 fill:#A5D6A7,color:#000,stroke:#388E3C
    style w2 fill:#A5D6A7,color:#000,stroke:#388E3C
    style w3 fill:#A5D6A7,color:#000,stroke:#388E3C
    style w4 fill:#A5D6A7,color:#000,stroke:#388E3C
    style w5 fill:#A5D6A7,color:#000,stroke:#388E3C
```

This diagram shows the primary data flow: audio input through n8n automation, API calls to Groq and GLPI, storage in databases, and monitoring visibility across all layers.

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
