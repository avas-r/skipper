# Skipper Architecture

## High-Level Overview

Skipper's architecture is divided into three main components:

1. **Control Plane**: Manages agent registration, authentication, scheduling, and monitoring
2. **Infrastructure**: Handles data storage, message passing, and credential management
3. **Endpoints**: Distributed agent clusters for executing tasks

```mermaid
flowchart LR
  subgraph ControlPlane
    UI[Web & API Portal]
    Auth[User Agent]
    Sched[Scheduler Agent]
    Exec[Execution Agent]
    Err[Error‑Handling Agent]
    Audit[Audit & Compliance Agent]
  end

  subgraph Infra
    Broker[(Message Broker)]
    Vault[(Credential Vault)]
    DB[(PostgreSQL DB)]
    ES[(Event Store)]
    Obs[(Observability Suite)]
  end

  subgraph Endpoints
    LA[Local Agent Cluster]
    LA -->|Heartbeats, Logs| Broker
    Broker --> Exec
    Exec --> LA
  end

  UI --> Auth --> DB
  Auth --> Sched
  Sched --> Broker
  Err --> Broker
  Audit --> ES
  Broker --> DB
  Broker --> Vault
  Obs <-- Broker
  Obs <-- LA
  Obs <-- DB
```

## Component Details

### Control Plane

- **Web & API Portal**: User interface for managing agents and viewing reports
- **User Agent**: Handles authentication and authorization
- **Scheduler Agent**: Distributes tasks among available agents
- **Execution Agent**: Monitors task execution and collects results
- **Error-Handling Agent**: Processes failures and retries
- **Audit & Compliance Agent**: Tracks all operations for compliance

### Infrastructure

- **Message Broker**: RabbitMQ for task distribution and event handling
- **Credential Vault**: HashiCorp Vault for secure credential management
- **PostgreSQL DB**: Persistent storage for agents, tasks, and results
- **Event Store**: Long-term storage for audit events
- **Observability Suite**: Prometheus/Grafana for metrics and monitoring

### Endpoints

- **Local Agent Cluster**: Distributed agents that execute tasks and report status

## Communication Patterns

1. **Command Flow**: UI → Auth → Scheduler → Broker → Local Agent
2. **Result Flow**: Local Agent → Broker → Execution Agent → DB
3. **Monitoring Flow**: Local Agent → Broker → Observability Suite
4. **Error Flow**: Local Agent → Broker → Error-Handling Agent → Scheduler

## Data Schema

[Include ERD or data model here]

## Security Architecture

[Detail security considerations and implementations]

## Scaling Considerations

[Document how components scale independently]
