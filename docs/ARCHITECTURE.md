# Otomeshon Architecture Guide

This document provides a comprehensive overview of the Otomeshon banking operations automation platform architecture, including system components, data flow, and integration patterns.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Patterns](#architecture-patterns)
- [Backend Services](#backend-services)
- [Frontend Architecture](#frontend-architecture)
- [Data Layer](#data-layer)
- [Integration Points](#integration-points)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)

## System Overview

Otomeshon is a microservices-based banking operations automation platform that streamlines post-trade processing through AI-powered workflows and provides advanced data analysis capabilities.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  Mobile Client  │    │  External APIs  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Load Balancer        │
                    │       (Traefik)           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Frontend Service      │
                    │    (React + TypeScript)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Backend API           │
                    │      (FastAPI)            │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────┴────────┐    ┌──────────┴──────────┐    ┌─────────┴────────┐
│   PostgreSQL   │    │      Redis          │    │      Neo4j       │
│   (Primary)    │    │    (Cache/Queue)    │    │  (Knowledge      │
│                │    │                     │    │   Graph)         │
└────────────────┘    └─────────────────────┘    └──────────────────┘
```

### Core Components

1. **Frontend Application**: React 18 + TypeScript SPA
2. **Backend API**: FastAPI Python application with async support
3. **Data Sandbox**: Advanced data analysis and visualization engine
4. **Knowledge Graph**: Neo4j-powered relationship mapping
5. **MCP Integration**: Multi-Channel Protocol for external data sources
6. **Workflow Engine**: LangGraph-based automation workflows
7. **AI Agents**: Configurable AI entities for task automation

## Architecture Patterns

### Microservices Architecture

The system follows a microservices pattern with clear service boundaries:

```
Backend Services:
├── DataSandboxService     # Data querying, transformation, export
├── MCPService            # External data provider integration
├── Neo4jService          # Knowledge graph operations
├── LLMService            # AI model abstraction layer
├── WebSocketService      # Real-time communication
├── TemporalService       # Workflow orchestration
├── KafkaService          # Event streaming
└── EmbeddingService      # Vector embeddings
```

### Event-Driven Architecture

```
┌─────────────┐    Events    ┌─────────────┐    Events    ┌─────────────┐
│   Service   │─────────────▶│    Kafka    │─────────────▶│   Service   │
│      A      │              │   Broker    │              │      B      │
└─────────────┘              └─────────────┘              └─────────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ Event Store │
                              │ (Persistent)│
                              └─────────────┘
```

### CQRS Pattern

The system implements Command Query Responsibility Segregation for data operations:

- **Commands**: Write operations through dedicated command handlers
- **Queries**: Read operations optimized for specific use cases
- **Event Sourcing**: Critical events stored for audit and replay

## Backend Services

### Core Service Layer

#### DataSandboxService
**Purpose**: Central service for data operations, querying, and analysis

**Key Responsibilities**:
- Data source management (Workflow, MCP, Agent, Manual)
- Advanced querying with filtering, sorting, pagination
- Data export in multiple formats (CSV, JSON, Excel)
- Data quality analysis and validation
- Real-time data streaming via WebSocket

**Integration Points**:
- PostgreSQL for data storage
- WebSocket for real-time updates
- External services for data ingestion

#### MCPService
**Purpose**: Integration with external financial data providers

**Key Responsibilities**:
- HTTP and WebSocket client implementations
- Server registration and health monitoring
- Tool calling and capability discovery
- Authentication and connection management

**Supported Protocols**:
- HTTP REST APIs
- WebSocket real-time streams
- Authentication: API Key, OAuth, Custom

#### Neo4jService
**Purpose**: Knowledge graph operations and relationship management

**Key Responsibilities**:
- Entity CRUD operations
- Relationship creation and querying
- Graph analytics and statistics
- Schema management and constraints

**Graph Schema**:
```cypher
// Core entity types
(Account)-[:HOLDS]->(Position)
(Position)-[:OF_SECURITY]->(Security)
(Trade)-[:EXECUTED_BY]->(Account)
(Workflow)-[:PROCESSES]->(Trade)
(Agent)-[:MONITORS]->(DataStream)
```

### Application Layer

#### Main Application (`main.py`)
**Full-featured backend** with all services:

```python
# Service initialization order
1. Database connection (PostgreSQL)
2. Neo4j knowledge graph
3. Knowledge graph sync service
4. Kafka event streaming
5. Temporal workflow engine
```

#### Simplified Application (`main_simple.py`)
**Development-focused backend** with minimal dependencies:

- In-memory data storage
- Sample data generation
- Core API endpoints
- No external service dependencies

### Configuration Management

Environment-based configuration using Pydantic settings:

```python
# Core settings categories
- Application: Environment, logging, debug mode
- Database: PostgreSQL, Redis, Neo4j connection strings
- External APIs: OpenAI, Anthropic API keys
- Services: Kafka, Temporal, Keycloak endpoints
- Observability: OpenTelemetry, LangSmith integration
```

## Frontend Architecture

### Component Hierarchy

```
App
├── Layout
│   ├── Navigation Drawer
│   ├── App Bar
│   └── Main Content Area
├── Pages
│   ├── Dashboard
│   ├── DataSandbox
│   ├── Agents
│   ├── KnowledgeGraph
│   ├── WorkflowBuilder
│   ├── DataIntegration
│   ├── Analytics
│   └── Settings
└── Shared Components
    ├── Charts (Recharts)
    ├── Data Tables (TanStack)
    ├── Forms (Material-UI)
    └── WebSocket Hooks
```

### State Management

- **Zustand**: Global application state
- **React Query**: Server state and caching
- **Local State**: Component-specific state with hooks

### Key Features

1. **Data Sandbox**: Advanced data analysis with TanStack Table
2. **Real-time Updates**: WebSocket integration for live data
3. **Chart Visualizations**: Recharts for data visualization
4. **Agent Chat Interface**: Conversational AI interactions
5. **Knowledge Graph UI**: Interactive network visualization

## Data Layer

### Database Architecture

#### PostgreSQL (Primary Database)
- **Purpose**: Transactional data, user management, application state
- **Tables**: Users, DataSources, DataRecords, Workflows, Agents
- **Features**: ACID compliance, complex queries, JSON support

#### Redis (Cache & Queue)
- **Purpose**: Session storage, caching, message queuing
- **Use Cases**: WebSocket connection management, temporary data
- **Features**: Pub/Sub, TTL, atomic operations

#### Neo4j (Knowledge Graph)
- **Purpose**: Entity relationships, graph analytics
- **Schema**: Financial entities and their relationships
- **Features**: Cypher queries, graph algorithms, constraints

### Data Flow Patterns

```
External Data Sources
        │
        ▼
┌─────────────────┐
│   MCP Service   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐
│ Data Sandbox    │───▶│   PostgreSQL    │
│   Service       │    │                 │
└─────────┬───────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │───▶│   Frontend      │
│   Service       │    │   Components    │
└─────────────────┘    └─────────────────┘
```

## Integration Points

### External Data Providers (MCP)

**Supported Provider Types**:
- Custodian banks (State Street, BNY Mellon)
- Market data providers (Bloomberg, Refinitiv)
- Pricing services
- Reference data providers
- Settlement systems

**Integration Patterns**:
- REST API polling
- WebSocket streaming
- Batch file processing
- Event-driven updates

### AI/ML Services

**LLM Integration**:
- OpenAI GPT models
- Anthropic Claude
- Local Ollama deployment

**Use Cases**:
- Document processing
- Workflow automation
- Conversational interfaces
- Data analysis assistance

### Workflow Orchestration

**Temporal Integration**:
- Long-running workflows
- Retry and error handling
- Workflow versioning
- Activity scheduling

**LangGraph Integration**:
- AI-powered decision making
- Multi-step processes
- Human-in-the-loop workflows

## Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Nginx) │  Backend (FastAPI) │  Databases        │
│  ├── React Build  │  ├── Gunicorn      │  ├── PostgreSQL   │
│  └── Static Files │  └── Workers       │  ├── Redis        │
│                   │                    │  └── Neo4j        │
├─────────────────────────────────────────────────────────────┤
│              Infrastructure Services                        │
│  ├── Traefik (Load Balancer)                              │
│  ├── Prometheus (Metrics)                                 │
│  ├── Grafana (Monitoring)                                 │
│  └── Jaeger (Tracing)                                     │
└─────────────────────────────────────────────────────────────┘
```

### Environment Configurations

1. **Development** (`docker-compose.dev.yml`): Full services with debugging
2. **Production** (`docker-compose.prod.yml`): Optimized with monitoring
3. **Testing** (`docker-compose.test.yml`): Isolated test environment

## Security Architecture

### Authentication & Authorization

- **Keycloak**: Identity and access management
- **JWT Tokens**: Stateless authentication
- **Role-based Access Control**: Fine-grained permissions

### Data Security

- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS/SSL for all communications
- **API Security**: Rate limiting, input validation
- **Secrets Management**: Environment-based configuration

### Network Security

- **Reverse Proxy**: Traefik with SSL termination
- **Internal Networks**: Docker network isolation
- **Firewall Rules**: Restricted port access
- **CORS Configuration**: Cross-origin request control

## Performance Considerations

### Scalability Patterns

- **Horizontal Scaling**: Multiple backend instances
- **Database Sharding**: Partitioned data storage
- **Caching Strategy**: Multi-level caching
- **Async Processing**: Non-blocking operations

### Monitoring & Observability

- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry + Jaeger
- **Logging**: Structured logging with correlation IDs
- **Health Checks**: Automated service monitoring

## Future Architecture Considerations

### Planned Enhancements

1. **Kubernetes Migration**: Container orchestration
2. **Event Sourcing**: Complete event-driven architecture
3. **API Gateway**: Centralized API management
4. **Service Mesh**: Advanced service communication
5. **Multi-tenancy**: Tenant isolation and scaling

### Technology Roadmap

- **Database**: Consider TimescaleDB for time-series data
- **Search**: Elasticsearch for advanced search capabilities
- **ML Pipeline**: MLflow for model management
- **Data Lake**: S3-compatible storage for large datasets
