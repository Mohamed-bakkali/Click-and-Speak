# Architecture

## High-Level System Design

```mermaid
flowchart TB
    subgraph user["User / Client"]
        audio["Audio Input<br/>Webhook /nouveau-ticket"]
    end

    subgraph automation["Automation Layer"]
        webhook["n8n Webhook<br/>/nouveau-ticket"]
        convert["Convert to MP3<br/>(if needed)"]
        whisper["Groq Whisper<br/>Speech-to-Text"]
        extract["Groq LLM<br/>Structured Ticket Data"]
        glpi["GLPI REST API<br/>Create Ticket"]
        log["Loki Log Entry"]
    end

    subgraph services["External Services"]
        groq["Groq Cloud API"]
        glpi_api["GLPI Application<br/>HTTP API"]
        mysql["MySQL Database"]
    end

    subgraph monitoring["Monitoring & Observability"]
        prometheus["Prometheus<br/>Metrics Scraper"]
        loki_store["Loki<br/>Log Store"]
        grafana["Grafana<br/>Dashboard"]
        promtail["Promtail<br/>Log Shipper"]
    end

    audio --> webhook --> convert --> whisper --> extract --> glpi
    glpi --> log
    whisper -.->|API call| groq
    extract -.->|API call| groq
    glpi -.->|HTTP| glpi_api
    glpi_api -->|R/W| mysql
    log -.->|push| loki_store
    prometheus -->|scrape| glpi_api
    promtail -->|ship| loki_store
    loki_store -->|query| grafana
    prometheus -->|query| grafana

    style user fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style automation fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style services fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style monitoring fill:#f3e5f5,stroke:#0277bd,stroke-width:2px
```

This diagram shows the path from incoming audio through n8n automation, external AI services, GLPI ticket creation, and monitoring data capture.

## Workflow Sequence

```mermaid
flowchart LR
    A["1. Receive Audio<br/>HTTP POST /nouveau-ticket"]
    B["2. Normalize Audio<br/>(.webm → .mp3)"]
    C["3. Transcribe<br/>Groq Whisper"]
    D["4. Extract Fields<br/>Groq LLM"]
    E["5. Format Payload<br/>Ticket JSON"]
    F["6. Authenticate<br/>GLPI Session"]
    G["7. Create Ticket<br/>POST /Ticket"]
    H["8. Record Log<br/>Loki Event"]
    I["9. Display Metrics<br/>Grafana Dashboard"]

    A --> B --> C --> D --> E --> F --> G --> H
    H --> I
    style A fill:#e1f5fe,stroke:#0288d1
    style C fill:#fff3e0,stroke:#ef6c00
    style D fill:#fff3e0,stroke:#ef6c00
    style F fill:#e8f5e9,stroke:#2e7d32
    style G fill:#e8f5e9,stroke:#2e7d32
    style H fill:#f1f8e9,stroke:#558b2f
    style I fill:#f3e5f5,stroke:#1565c0
```

The workflow breaks down the key steps in the n8n automation path: audio intake, AI transcription, extraction, ticket creation, and logging.

## Container Networking

```mermaid
flowchart TB
    subgraph host["Local Docker Host"]
        n8n["n8n<br/>localhost:5678"]
        glpi["GLPI<br/>localhost:8080"]
        grafana["Grafana<br/>localhost:3000"]
        prometheus["Prometheus<br/>localhost:9090"]
        loki["Loki<br/>localhost:3100"]
        app["Dashboard App<br/>internal:80"]
    end

    subgraph external["External API"]
        groq["Groq API<br/>api.groq.com"]
    end

    n8n -->|GLPI API| glpi
    n8n -->|Groq API| groq
    n8n -->|Loki Push| loki
    glpi -->|MySQL| mysql["MySQL<br/>container"]
    prometheus -->|scrape| n8n
    prometheus -->|scrape| app
    promtail["Promtail"] -->|push| loki
    grafana -->|query| prometheus
    grafana -->|query| loki

    style host fill:#f3f4f6,stroke:#90a4ae,stroke-width:1px
    style external fill:#fff8e1,stroke:#ff8f00,stroke-width:1px
    style n8n fill:#bbdefb,stroke:#1976d2
    style glpi fill:#c8e6c9,stroke:#388e3c
    style grafana fill:#ffe0b2,stroke:#f57c00
    style prometheus fill:#fff9c4,stroke:#fbc02d
    style loki fill:#dcedc8,stroke:#558b2f
    style mysql fill:#f0f4c3,stroke:#7cb342
```

This network diagram documents how local containers are exposed, which services scrape metrics, and which external API is required.

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
flowchart LR
    subgraph ingestion["Metrics & Logs Ingestion"]
        n8n_metrics["n8n /metrics"]
        app_metrics["Dashboard App /metrics"]
        container_logs["Container Logs"]
    end

    subgraph aggregation["Aggregation"]
        prometheus["Prometheus"]
        promtail["Promtail"]
        loki["Loki"]
    end

    subgraph visualization["Visualization"]
        grafana["Grafana"]
    end

    n8n_metrics --> prometheus
    app_metrics --> prometheus
    container_logs --> promtail --> loki
    prometheus --> grafana
    loki --> grafana

    style ingestion fill:#e3f2fd,stroke:#1976d2
    style aggregation fill:#f3e5f5,stroke:#7b1fa2
    style visualization fill:#e8f5e9,stroke:#2e7d32
```

The monitoring flow clarifies where metrics and logs are collected, aggregated, and surfaced in Grafana.

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
