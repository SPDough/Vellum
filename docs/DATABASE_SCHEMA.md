# Otomeshon Database Schema Documentation

This document provides comprehensive documentation of the database schemas used in the Otomeshon banking operations automation platform.

## Table of Contents

- [Overview](#overview)
- [PostgreSQL Schema](#postgresql-schema)
- [Neo4j Graph Schema](#neo4j-graph-schema)
- [Redis Data Structures](#redis-data-structures)
- [Data Relationships](#data-relationships)
- [Migration Procedures](#migration-procedures)
- [Performance Considerations](#performance-considerations)

## Overview

Otomeshon uses a multi-database architecture to handle different types of data efficiently:

- **PostgreSQL**: Primary relational database for transactional data
- **Neo4j**: Graph database for entity relationships and knowledge graph
- **Redis**: In-memory store for caching and session management

## PostgreSQL Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

#### Data Sources Table
```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'workflow', 'mcp', 'agent', 'manual'
    description TEXT,
    schema JSONB,
    source_metadata JSONB DEFAULT '{}',
    config JSONB DEFAULT '{}',
    record_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_sources_type ON data_sources(type);
CREATE INDEX idx_data_sources_status ON data_sources(status);
CREATE INDEX idx_data_sources_created_by ON data_sources(created_by);
CREATE INDEX idx_data_sources_metadata ON data_sources USING GIN(source_metadata);
```

#### Data Records Table
```sql
CREATE TABLE data_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_records_source_id ON data_records(data_source_id);
CREATE INDEX idx_data_records_timestamp ON data_records(timestamp);
CREATE INDEX idx_data_records_data ON data_records USING GIN(data);
CREATE INDEX idx_data_records_metadata ON data_records USING GIN(metadata);

-- Partitioning by month for better performance
CREATE TABLE data_records_y2024m01 PARTITION OF data_records
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

#### Workflows Table
```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'active', 'inactive', 'archived'
    schedule VARCHAR(255), -- Cron expression
    enabled BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_enabled ON workflows(enabled);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);
```

#### MCP Servers Table
```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL, -- 'custodian', 'market_data', 'pricing'
    base_url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50) NOT NULL, -- 'none', 'api_key', 'oauth'
    auth_config JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'disconnected', -- 'connected', 'disconnected', 'error'
    enabled BOOLEAN DEFAULT true,
    last_health_check TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mcp_servers_provider_type ON mcp_servers(provider_type);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);
CREATE INDEX idx_mcp_servers_enabled ON mcp_servers(enabled);
```

## Neo4j Graph Schema

### Node Types

#### Entity Nodes
```cypher
// Core entity constraint
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS 
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// Entity properties
(:Entity {
  id: "string",           // Unique identifier
  type: "string",         // Entity type
  name: "string",         // Display name
  properties: {},         // Additional properties
  created_at: "datetime",
  updated_at: "datetime"
})
```

#### Account Nodes
```cypher
CREATE CONSTRAINT account_id_unique IF NOT EXISTS 
FOR (a:Account) REQUIRE a.id IS UNIQUE;

(:Account {
  id: "string",
  name: "string",
  account_type: "string", // 'trading', 'settlement', 'custody'
  balance: "float",
  currency: "string",
  status: "string",       // 'active', 'inactive', 'closed'
  created_at: "datetime",
  updated_at: "datetime"
})
```

#### Position Nodes
```cypher
CREATE CONSTRAINT position_id_unique IF NOT EXISTS 
FOR (p:Position) REQUIRE p.id IS UNIQUE;

(:Position {
  id: "string",
  quantity: "float",
  market_value: "float",
  cost_basis: "float",
  currency: "string",
  position_date: "date",
  created_at: "datetime",
  updated_at: "datetime"
})
```

### Relationship Types

#### Account Relationships
```cypher
// Account holds positions
(a:Account)-[:HOLDS {
  quantity: "float",
  acquisition_date: "date",
  cost_basis: "float"
}]->(p:Position)

// Account executes trades
(a:Account)-[:EXECUTES {
  execution_time: "datetime",
  commission: "float"
}]->(t:Trade)
```

### Common Queries

#### Find Account Holdings
```cypher
MATCH (a:Account {id: $account_id})-[:HOLDS]->(p:Position)-[:OF_SECURITY]->(s:Security)
RETURN a.name as account_name, 
       p.quantity, 
       p.market_value, 
       s.symbol, 
       s.name as security_name
ORDER BY p.market_value DESC;
```

## Redis Data Structures

### Session Management
```redis
# User sessions
SET session:{session_id} "{user_id: 'uuid', expires_at: 'timestamp'}" EX 3600

# User preferences
HSET user:{user_id}:preferences theme "dark" language "en" timezone "UTC"
```

### WebSocket Connections
```redis
# Active WebSocket connections
SADD websocket:connections:{source_id} {connection_id}
SET websocket:connection:{connection_id} "{user_id: 'uuid', connected_at: 'timestamp'}" EX 7200
```

### Caching
```redis
# API response caching
SET cache:data_sources "{json_data}" EX 300
SET cache:mcp_servers "{json_data}" EX 600

# Query result caching
SET cache:query:{hash} "{query_result}" EX 900
```

## Data Relationships

### Cross-Database Relationships

#### PostgreSQL to Neo4j Sync
```python
# Sync data from PostgreSQL to Neo4j
def sync_account_to_graph(account_id: str):
    # Fetch from PostgreSQL
    account = db.query(Account).filter(Account.id == account_id).first()
    
    # Create/update in Neo4j
    neo4j_service.create_or_update_entity(
        entity_type="Account",
        entity_id=account.id,
        properties={
            "name": account.name,
            "account_type": account.account_type,
            "balance": account.balance,
            "currency": account.currency,
            "status": account.status
        }
    )
```

### Data Flow Patterns

#### Real-time Data Pipeline
```
MCP Server → Redis Stream → PostgreSQL → Neo4j → WebSocket → Frontend
     ↓
Data Validation → Data Transformation → Data Storage → Graph Update → UI Update
```

## Migration Procedures

### PostgreSQL Migrations

#### Migration File Structure
```sql
-- migrations/001_initial_schema.sql
BEGIN;

-- Create tables
CREATE TABLE users (...);
CREATE TABLE data_sources (...);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);

-- Insert initial data
INSERT INTO users (username, email, role) VALUES 
('admin', 'admin@otomeshon.com', 'admin');

COMMIT;
```

### Neo4j Schema Updates

#### Schema Migration Script
```cypher
// migrations/neo4j/001_initial_constraints.cypher

// Create constraints
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS 
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT account_id_unique IF NOT EXISTS 
FOR (a:Account) REQUIRE a.id IS UNIQUE;

// Create indexes
CREATE INDEX entity_type_index IF NOT EXISTS 
FOR (e:Entity) ON (e.type);
```

## Performance Considerations

### PostgreSQL Optimization

#### Partitioning Strategy
```sql
-- Partition data_records by month
CREATE TABLE data_records (
    id UUID DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL,
    data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE data_records_y2024m01 PARTITION OF data_records
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

#### Index Optimization
```sql
-- Composite indexes for common queries
CREATE INDEX idx_data_records_source_timestamp 
ON data_records(data_source_id, timestamp DESC);

-- GIN indexes for JSONB queries
CREATE INDEX idx_data_records_data_gin 
ON data_records USING GIN(data);
```

### Neo4j Performance

#### Query Optimization
```cypher
// Use PROFILE to analyze query performance
PROFILE MATCH (a:Account)-[:HOLDS]->(p:Position)-[:OF_SECURITY]->(s:Security)
WHERE a.balance > 1000000
RETURN a, p, s;

// Optimize with proper indexes
CREATE INDEX account_balance_index IF NOT EXISTS 
FOR (a:Account) ON (a.balance);
```

### Redis Optimization

#### Memory Management
```redis
# Configure memory policies
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru

# Use appropriate data structures
# For small sets, use hash instead of separate keys
HSET user:123 name "John" email "john@example.com"
```

This comprehensive database schema documentation provides a complete reference for understanding and working with the Otomeshon platform's data layer.
