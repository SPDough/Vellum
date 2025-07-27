# Otomeshon Monitoring and Observability Guide

This document provides comprehensive guidance for monitoring, observability, and operational insights for the Otomeshon banking operations automation platform.

## Table of Contents

- [Overview](#overview)
- [Metrics Collection](#metrics-collection)
- [Logging Strategy](#logging-strategy)
- [Distributed Tracing](#distributed-tracing)
- [Health Checks](#health-checks)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Performance Monitoring](#performance-monitoring)
- [Security Monitoring](#security-monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

Otomeshon implements a comprehensive observability stack using:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Centralized logging (Elasticsearch, Logstash, Kibana)
- **OpenTelemetry**: Unified observability framework

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   OpenTelemetry │───▶│   Prometheus    │
│   (Metrics)     │    │    Collector    │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
┌─────────────────┐             │               ┌─────────────────┐
│   Application   │─────────────┘               │     Grafana     │
│   (Traces)      │                             │  (Visualization)│
└─────────────────┘                             └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│   Application   │───▶│   Logstash      │───▶ ┌─────────────────┐
│   (Logs)        │    │  (Processing)   │     │   Alertmanager  │
└─────────────────┘    └─────────────────┘     │   (Alerting)    │
                                │               └─────────────────┘
                        ┌─────────────────┐
                        │  Elasticsearch  │
                        │   (Storage)     │
                        └─────────────────┘
```

## Metrics Collection

### Application Metrics

#### Backend Metrics (FastAPI)

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database Metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# Business Metrics
data_sandbox_queries_total = Counter(
    'data_sandbox_queries_total',
    'Total data sandbox queries',
    ['source_type', 'user_id']
)

mcp_server_requests_total = Counter(
    'mcp_server_requests_total',
    'Total MCP server requests',
    ['server_id', 'status']
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)
```

#### Metrics Middleware

```python
# app/middleware/metrics.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
```

### Frontend Metrics

#### Web Vitals Monitoring

```typescript
// src/utils/metrics.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

interface MetricData {
  name: string;
  value: number;
  id: string;
  delta: number;
}

const sendMetric = (metric: MetricData) => {
  fetch('/api/v1/metrics/web-vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric)
  });
};

// Collect Web Vitals
getCLS(sendMetric);
getFID(sendMetric);
getFCP(sendMetric);
getLCP(sendMetric);
getTTFB(sendMetric);
```

### Infrastructure Metrics

#### Docker Container Metrics

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  prometheus_data:
  grafana_data:
```

## Logging Strategy

### Structured Logging

#### Backend Logging Configuration

```python
# app/core/logging.py
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'otomeshon-backend'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

#### Frontend Logging

```typescript
// src/utils/logger.ts
interface LogEntry {
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: string;
  context?: Record<string, any>;
  userId?: string;
  sessionId?: string;
}

class Logger {
  private sessionId: string;
  private userId?: string;

  constructor() {
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private createLogEntry(level: LogEntry['level'], message: string, context?: Record<string, any>): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
      userId: this.userId,
      sessionId: this.sessionId
    };
  }

  private sendLog(entry: LogEntry) {
    fetch('/api/v1/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    }).catch(err => {
      console.error('Failed to send log:', err);
    });

    if (process.env.NODE_ENV === 'development') {
      console[entry.level](entry.message, entry.context);
    }
  }

  info(message: string, context?: Record<string, any>) {
    this.sendLog(this.createLogEntry('info', message, context));
  }

  error(message: string, context?: Record<string, any>) {
    this.sendLog(this.createLogEntry('error', message, context));
  }
}

export const logger = new Logger();
```

## Health Checks

### Application Health Checks

#### Backend Health Endpoint

```python
# app/api/endpoints/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check():
    return {"status": "alive"}
```

## Alerting

### Alert Rules Configuration

```yaml
# monitoring/alert_rules.yml
groups:
  - name: otomeshon_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"
```

## Dashboards

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Otomeshon Application Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

## Performance Monitoring

### Application Performance Monitoring

```python
# app/core/performance.py
import time
import psutil
from functools import wraps
from prometheus_client import Histogram, Gauge

function_duration = Histogram(
    'function_duration_seconds',
    'Function execution time',
    ['function_name', 'module']
)

memory_usage = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            function_duration.labels(
                function_name=func.__name__,
                module=func.__module__
            ).observe(duration)
    
    return wrapper
```

## Security Monitoring

### Security Event Logging

```python
# app/core/security_monitoring.py
import logging
from fastapi import Request
from datetime import datetime

security_logger = logging.getLogger("security")

class SecurityEvent:
    def __init__(self, event_type: str, request: Request, details: dict = None):
        self.event_type = event_type
        self.timestamp = datetime.utcnow()
        self.ip_address = request.client.host
        self.user_agent = request.headers.get("user-agent")
        self.details = details or {}

    def log(self):
        security_logger.warning(
            f"Security event: {self.event_type}",
            extra={
                "event_type": self.event_type,
                "timestamp": self.timestamp.isoformat(),
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "details": self.details
            }
        )

def log_failed_login(request: Request, username: str):
    event = SecurityEvent(
        "failed_login",
        request,
        {"username": username}
    )
    event.log()
```

This comprehensive monitoring and observability guide provides all the tools and configurations needed to effectively monitor the Otomeshon platform in production, ensuring high availability, performance, and security.
