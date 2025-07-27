# Otomeshon API Reference

This document provides comprehensive documentation for all API endpoints in the Otomeshon banking operations automation platform.

## Table of Contents

- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Data Sandbox API](#data-sandbox-api)
- [MCP Servers API](#mcp-servers-api)
- [Knowledge Graph API](#knowledge-graph-api)
- [Workflows API](#workflows-api)
- [Data Streams API](#data-streams-api)
- [WebSocket Endpoints](#websocket-endpoints)
- [Health & Monitoring](#health--monitoring)

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`
- **API Prefix**: `/api/v1`

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": { ... },
  "message": "Success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `AUTHENTICATION_REQUIRED` - Valid authentication token required
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Data Sandbox API

The Data Sandbox API provides comprehensive data management, querying, and analysis capabilities.

### Data Sources

#### List Data Sources

```http
GET /api/v1/data-sandbox/sources
```

**Response:**
```json
{
  "data": [
    {
      "id": "ds_123",
      "name": "Trade Data",
      "type": "workflow",
      "description": "Post-trade settlement data",
      "record_count": 1250,
      "last_updated": "2024-01-15T10:30:00Z",
      "status": "active",
      "schema": {
        "fields": [
          {"name": "trade_id", "type": "string"},
          {"name": "amount", "type": "number"},
          {"name": "currency", "type": "string"}
        ]
      }
    }
  ]
}
```

#### Create Data Source

```http
POST /api/v1/data-sandbox/sources
Content-Type: application/json

{
  "name": "New Data Source",
  "type": "manual",
  "description": "Manually created data source",
  "schema": {
    "fields": [
      {"name": "id", "type": "string"},
      {"name": "value", "type": "number"}
    ]
  }
}
```

#### Get Data Source

```http
GET /api/v1/data-sandbox/sources/{source_id}
```

#### Update Data Source

```http
PUT /api/v1/data-sandbox/sources/{source_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### Delete Data Source

```http
DELETE /api/v1/data-sandbox/sources/{source_id}
```

### Data Querying

#### Query Data

```http
POST /api/v1/data-sandbox/query
Content-Type: application/json

{
  "source": "ds_123",
  "filters": [
    {
      "field": "amount",
      "operator": "gt",
      "value": 1000
    },
    {
      "field": "currency",
      "operator": "eq",
      "value": "USD"
    }
  ],
  "sorts": [
    {
      "field": "trade_date",
      "direction": "desc"
    }
  ],
  "limit": 100,
  "offset": 0,
  "fields": ["trade_id", "amount", "currency", "trade_date"]
}
```

**Response:**
```json
{
  "data": [
    {
      "trade_id": "T123456",
      "amount": 15000.50,
      "currency": "USD",
      "trade_date": "2024-01-15T09:30:00Z"
    }
  ],
  "total_count": 1250,
  "execution_time": 0.045,
  "schema": {
    "fields": [...]
  }
}
```

#### Filter Operators

- `eq` - Equal to
- `ne` - Not equal to
- `gt` - Greater than
- `gte` - Greater than or equal to
- `lt` - Less than
- `lte` - Less than or equal to
- `in` - In list of values
- `like` - Text contains (case-insensitive)
- `regex` - Regular expression match

#### Get Data Preview

```http
GET /api/v1/data-sandbox/sources/{source_id}/preview?limit=100
```

### Data Export

#### Export Data

```http
POST /api/v1/data-sandbox/export
Content-Type: application/json

{
  "query": {
    "source": "ds_123",
    "filters": [...],
    "limit": 10000
  },
  "format": "csv",
  "filename": "trade_data_export.csv"
}
```

**Supported Formats:**
- `csv` - Comma-separated values
- `json` - JSON format
- `xlsx` - Excel spreadsheet

**Response:** File download with appropriate content-type headers.

### Workflow Integration

#### Get Workflow Outputs

```http
GET /api/v1/data-sandbox/workflow-outputs?workflow_id=wf_123&limit=50
```

#### Create Data Source from Workflow

```http
POST /api/v1/data-sandbox/sources/from-workflow
Content-Type: application/json

{
  "workflow_id": "wf_123",
  "output_name": "processed_trades"
}
```

### MCP Integration

#### Get MCP Data Streams

```http
GET /api/v1/data-sandbox/mcp-streams?server_id=mcp_server_1&limit=50
```

#### Create Data Source from MCP

```http
POST /api/v1/data-sandbox/sources/from-mcp
Content-Type: application/json

{
  "server_id": "mcp_server_1",
  "stream_name": "market_data_feed"
}
```

### Agent Integration

#### Get Agent Results

```http
GET /api/v1/data-sandbox/agent-results?agent_id=agent_123&limit=50
```

### Data Quality

#### Analyze Data Quality

```http
GET /api/v1/data-sandbox/sources/{source_id}/quality
```

**Response:**
```json
{
  "completeness": 95.5,
  "accuracy": 98.2,
  "consistency": 92.1,
  "timeliness": 88.7,
  "issues": [
    {
      "type": "missing_values",
      "count": 15,
      "description": "Column 'customer_id' has 15 missing values",
      "affected_fields": ["customer_id"]
    }
  ]
}
```

### Data Transformations

#### Transform Data

```http
POST /api/v1/data-sandbox/sources/{source_id}/transform
Content-Type: application/json

{
  "transformations": [
    {
      "type": "filter",
      "condition": "amount > 1000"
    },
    {
      "type": "aggregate",
      "group_by": ["currency"],
      "aggregations": {
        "total_amount": "sum(amount)",
        "trade_count": "count(*)"
      }
    }
  ]
}
```

## MCP Servers API

Manage connections to external Multi-Channel Protocol servers.

### List MCP Servers

```http
GET /api/v1/mcp-servers?provider_type=custodian&enabled_only=true
```

**Response:**
```json
{
  "data": [
    {
      "id": "mcp_1",
      "name": "State Street Custodian",
      "provider_type": "custodian",
      "base_url": "https://api.statestreet.com/mcp",
      "status": "connected",
      "capabilities": ["trade_data", "position_data", "settlement"],
      "last_health_check": "2024-01-15T10:25:00Z",
      "enabled": true
    }
  ]
}
```

### Create MCP Server

```http
POST /api/v1/mcp-servers
Content-Type: application/json

{
  "name": "Bloomberg Market Data",
  "provider_type": "market_data",
  "base_url": "https://api.bloomberg.com/mcp",
  "auth_type": "api_key",
  "auth_config": {
    "api_key": "your-api-key"
  },
  "capabilities": ["real_time_prices", "historical_data"],
  "description": "Bloomberg market data feed"
}
```

### Get MCP Server

```http
GET /api/v1/mcp-servers/{server_id}
```

### Update MCP Server

```http
PUT /api/v1/mcp-servers/{server_id}
Content-Type: application/json

{
  "name": "Updated Server Name",
  "enabled": false
}
```

### Delete MCP Server

```http
DELETE /api/v1/mcp-servers/{server_id}
```

### Test MCP Server Connection

```http
POST /api/v1/mcp-servers/{server_id}/test
```

**Response:**
```json
{
  "server_id": "mcp_1",
  "success": true,
  "response_time_ms": 245,
  "capabilities_discovered": ["trade_data", "position_data"],
  "tested_at": "2024-01-15T10:30:00Z"
}
```

### Get Server Capabilities

```http
GET /api/v1/mcp-servers/{server_id}/capabilities
```

### Get Server Metrics

```http
GET /api/v1/mcp-servers/{server_id}/metrics
```

**Response:**
```json
{
  "server_id": "mcp_1",
  "total_requests": 1250,
  "successful_requests": 1180,
  "failed_requests": 70,
  "average_response_time_ms": 245.5,
  "last_24h_requests": 180,
  "uptime_percentage": 94.4
}
```

## Knowledge Graph API

Interact with the Neo4j knowledge graph for entity relationships.

### Create Entity

```http
POST /api/v1/knowledge-graph/entities
Content-Type: application/json

{
  "type": "Account",
  "properties": {
    "id": "ACC_123",
    "name": "Trading Account A",
    "account_type": "trading",
    "balance": 1000000.00,
    "currency": "USD"
  }
}
```

### Get Entity

```http
GET /api/v1/knowledge-graph/entities/{entity_type}/{entity_id}
```

### Update Entity

```http
PUT /api/v1/knowledge-graph/entities/{entity_type}/{entity_id}
Content-Type: application/json

{
  "properties": {
    "balance": 1250000.00,
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

### Delete Entity

```http
DELETE /api/v1/knowledge-graph/entities/{entity_type}/{entity_id}
```

### Create Relationship

```http
POST /api/v1/knowledge-graph/relationships
Content-Type: application/json

{
  "from_entity_type": "Account",
  "from_entity_id": "ACC_123",
  "to_entity_type": "Position",
  "to_entity_id": "POS_456",
  "relationship_type": "HOLDS",
  "properties": {
    "quantity": 1000,
    "acquisition_date": "2024-01-10T00:00:00Z"
  }
}
```

### Get Entity Relationships

```http
GET /api/v1/knowledge-graph/entities/{entity_type}/{entity_id}/relationships?direction=both
```

### Execute Cypher Query

```http
POST /api/v1/knowledge-graph/cypher
Content-Type: application/json

{
  "query": "MATCH (a:Account)-[:HOLDS]->(p:Position) WHERE a.balance > $min_balance RETURN a, p",
  "parameters": {
    "min_balance": 500000
  }
}
```

### Get Graph Statistics

```http
GET /api/v1/knowledge-graph/stats
```

**Response:**
```json
{
  "total_nodes": 15420,
  "total_relationships": 28350,
  "node_types": [
    {"label": "Account", "count": 1250},
    {"label": "Position", "count": 5680},
    {"label": "Security", "count": 2340}
  ],
  "relationship_types": [
    {"type": "HOLDS", "count": 12500},
    {"type": "EXECUTES", "count": 8900}
  ]
}
```

## Workflows API

Manage and execute automated workflows.

### List Workflows

```http
GET /api/v1/workflows?status=active&limit=50
```

### Create Workflow

```http
POST /api/v1/workflows
Content-Type: application/json

{
  "name": "Trade Settlement Workflow",
  "description": "Automated post-trade settlement process",
  "definition": {
    "steps": [
      {
        "name": "validate_trade",
        "type": "validation",
        "config": {...}
      },
      {
        "name": "update_positions",
        "type": "data_update",
        "config": {...}
      }
    ]
  },
  "schedule": "0 9 * * 1-5",
  "enabled": true
}
```

### Get Workflow

```http
GET /api/v1/workflows/{workflow_id}
```

### Execute Workflow

```http
POST /api/v1/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input_data": {
    "trade_date": "2024-01-15",
    "batch_id": "BATCH_123"
  }
}
```

### Get Workflow Executions

```http
GET /api/v1/workflows/{workflow_id}/executions?limit=20
```

## Data Streams API

Manage real-time data streams.

### List Data Streams

```http
GET /api/v1/data-streams?status=active
```

### Create Data Stream

```http
POST /api/v1/data-streams
Content-Type: application/json

{
  "name": "Market Data Stream",
  "source_type": "mcp",
  "source_config": {
    "server_id": "mcp_1",
    "stream_name": "real_time_prices"
  },
  "enabled": true
}
```

### Get Data Stream

```http
GET /api/v1/data-streams/{stream_id}
```

### Start Data Stream

```http
POST /api/v1/data-streams/{stream_id}/start
```

### Stop Data Stream

```http
POST /api/v1/data-streams/{stream_id}/stop
```

### Get Stream Metrics

```http
GET /api/v1/data-streams/{stream_id}/metrics
```

## WebSocket Endpoints

Real-time communication endpoints using WebSocket protocol.

### Data Sandbox WebSocket

```javascript
// Connect to specific data source updates
const ws = new WebSocket('ws://localhost:8000/api/v1/data-sandbox/sources/{source_id}/ws?user_id=user123');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received update:', data);
};

// Message types:
// - data_update: New data available
// - source_status: Data source status change
// - export_complete: Data export finished
```

### Global Data Sandbox WebSocket

```javascript
// Connect to all data sandbox updates
const ws = new WebSocket('ws://localhost:8000/api/v1/data-sandbox/ws?user_id=user123');
```

### WebSocket Message Format

```json
{
  "type": "data_update",
  "source_id": "ds_123",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "new_records": 15,
    "updated_records": 3
  }
}
```

### WebSocket Connection Stats

```http
GET /api/v1/data-sandbox/ws/stats
```

**Response:**
```json
{
  "active_connections": 25,
  "total_messages_sent": 15420,
  "connections_by_source": {
    "ds_123": 8,
    "ds_456": 12
  }
}
```

## Health & Monitoring

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "otomeshon-api",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy",
    "neo4j": "healthy"
  }
}
```

### Metrics Endpoint

```http
GET /metrics
```

**Response:** Prometheus-formatted metrics

```
# HELP otomeshon_websocket_connections_total Total WebSocket connections
# TYPE otomeshon_websocket_connections_total counter
otomeshon_websocket_connections_total 25

# HELP otomeshon_data_sandbox_records_total Total data sandbox records
# TYPE otomeshon_data_sandbox_records_total gauge
otomeshon_data_sandbox_records_total 125000

# HELP otomeshon_data_exports_total Total data exports
# TYPE otomeshon_data_exports_total counter
otomeshon_data_exports_total 1250
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Default**: 100 requests per minute per user
- **Data Export**: 10 requests per minute per user
- **WebSocket**: 5 connections per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## SDK and Client Libraries

Official client libraries are available for:
- **Python**: `pip install otomeshon-client`
- **JavaScript/TypeScript**: `npm install @otomeshon/client`
- **Java**: Maven/Gradle dependency available

### Python Example

```python
from otomeshon_client import OtomeshonClient

client = OtomeshonClient(
    base_url="https://api.otomeshon.com",
    api_key="your-api-key"
)

# Query data
result = client.data_sandbox.query(
    source="ds_123",
    filters=[{"field": "amount", "operator": "gt", "value": 1000}],
    limit=100
)

print(f"Found {result.total_count} records")
```

### JavaScript Example

```javascript
import { OtomeshonClient } from '@otomeshon/client';

const client = new OtomeshonClient({
  baseUrl: 'https://api.otomeshon.com',
  apiKey: 'your-api-key'
});

// Query data
const result = await client.dataSandbox.query({
  source: 'ds_123',
  filters: [{ field: 'amount', operator: 'gt', value: 1000 }],
  limit: 100
});

console.log(`Found ${result.totalCount} records`);
```
