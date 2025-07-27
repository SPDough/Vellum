# Otomeshon Troubleshooting Guide

This document provides solutions to common issues encountered when developing, deploying, and operating the Otomeshon banking operations automation platform.

## Table of Contents

- [Development Environment Issues](#development-environment-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Database Issues](#database-issues)
- [Integration Issues](#integration-issues)
- [Performance Issues](#performance-issues)
- [Production Issues](#production-issues)
- [Monitoring and Debugging](#monitoring-and-debugging)

## Development Environment Issues

### Python Environment Issues

#### Issue: Virtual environment activation fails
```bash
Error: cannot activate virtual environment
```

**Solutions:**
1. Recreate virtual environment:
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

2. Check Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

3. Install virtualenv if missing:
   ```bash
   pip install virtualenv
   ```

#### Issue: Package installation fails
```bash
ERROR: Could not install packages due to an EnvironmentError
```

**Solutions:**
1. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

2. Clear pip cache:
   ```bash
   pip cache purge
   ```

3. Install with no cache:
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

4. Check for conflicting packages:
   ```bash
   pip check
   ```

### Node.js Environment Issues

#### Issue: Node modules installation fails
```bash
npm ERR! peer dep missing
```

**Solutions:**
1. Clear npm cache:
   ```bash
   npm cache clean --force
   ```

2. Delete node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Use specific Node version:
   ```bash
   nvm use 18
   npm install
   ```

4. Install with legacy peer deps:
   ```bash
   npm install --legacy-peer-deps
   ```

### Docker Issues

#### Issue: Docker containers fail to start
```bash
Error: port already in use
```

**Solutions:**
1. Check port usage:
   ```bash
   lsof -i :8000  # Check specific port
   netstat -tulpn | grep :8000
   ```

2. Stop conflicting services:
   ```bash
   docker-compose down
   sudo systemctl stop postgresql
   ```

3. Use different ports:
   ```bash
   # Edit docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

#### Issue: Docker build fails
```bash
Error: failed to solve with frontend dockerfile.v0
```

**Solutions:**
1. Clear Docker cache:
   ```bash
   docker system prune -a
   ```

2. Build with no cache:
   ```bash
   docker-compose build --no-cache
   ```

3. Check Dockerfile syntax:
   ```bash
   docker build --dry-run .
   ```

## Backend Issues

### FastAPI Issues

#### Issue: Server fails to start
```bash
ImportError: No module named 'app'
```

**Solutions:**
1. Check PYTHONPATH:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
   ```

2. Run from correct directory:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

#### Issue: Database connection fails
```bash
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
1. Check database is running:
   ```bash
   docker-compose ps postgres
   pg_isready -h localhost -p 5432
   ```

2. Verify connection string:
   ```bash
   # Check .env file
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

3. Test connection manually:
   ```bash
   psql postgresql://user:password@localhost:5432/dbname
   ```

4. Check firewall/network:
   ```bash
   telnet localhost 5432
   ```

### Authentication Issues

#### Issue: JWT token validation fails
```bash
HTTPException: Could not validate credentials
```

**Solutions:**
1. Check JWT secret key:
   ```python
   # Ensure SECRET_KEY is set in environment
   SECRET_KEY=your-secret-key-here
   ```

2. Verify token format:
   ```bash
   # Token should be: Bearer <jwt-token>
   curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
   ```

3. Check token expiration:
   ```python
   import jwt
   decoded = jwt.decode(token, verify=False)
   print(decoded['exp'])  # Check expiration timestamp
   ```

### API Issues

#### Issue: CORS errors
```bash
Access to fetch blocked by CORS policy
```

**Solutions:**
1. Configure CORS in FastAPI:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. Check frontend URL:
   ```javascript
   // Ensure API calls use correct base URL
   const API_BASE = process.env.VITE_API_URL || 'http://localhost:8000';
   ```

#### Issue: Validation errors
```bash
422 Unprocessable Entity: validation error
```

**Solutions:**
1. Check request payload:
   ```bash
   curl -X POST http://localhost:8000/api/endpoint \
     -H "Content-Type: application/json" \
     -d '{"field": "value"}'
   ```

2. Verify Pydantic models:
   ```python
   # Check model definition matches request
   class RequestModel(BaseModel):
       field: str
       optional_field: Optional[int] = None
   ```

3. Enable detailed error messages:
   ```python
   # In FastAPI app
   app = FastAPI(debug=True)
   ```

## Frontend Issues

### React Development Issues

#### Issue: Component not rendering
```bash
Warning: React.createElement: type is invalid
```

**Solutions:**
1. Check import statements:
   ```typescript
   // Correct import
   import { Component } from './Component';
   
   // Not default export
   import Component from './Component';  // Wrong if not default
   ```

2. Verify component export:
   ```typescript
   // Named export
   export const Component = () => { ... };
   
   // Default export
   const Component = () => { ... };
   export default Component;
   ```

3. Check for circular imports:
   ```bash
   # Use madge to detect circular dependencies
   npx madge --circular src/
   ```

#### Issue: TypeScript compilation errors
```bash
TS2307: Cannot find module or its corresponding type declarations
```

**Solutions:**
1. Install type definitions:
   ```bash
   npm install --save-dev @types/node @types/react
   ```

2. Check tsconfig.json:
   ```json
   {
     "compilerOptions": {
       "moduleResolution": "node",
       "esModuleInterop": true,
       "allowSyntheticDefaultImports": true
     }
   }
   ```

3. Restart TypeScript server:
   ```bash
   # In VS Code: Ctrl+Shift+P -> "TypeScript: Restart TS Server"
   ```

### Build Issues

#### Issue: Build fails with memory error
```bash
FATAL ERROR: Ineffective mark-compacts near heap limit
```

**Solutions:**
1. Increase Node memory:
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm run build
   ```

2. Use build optimization:
   ```json
   // package.json
   "scripts": {
     "build": "vite build --mode production"
   }
   ```

3. Analyze bundle size:
   ```bash
   npm run build -- --analyze
   ```

### State Management Issues

#### Issue: Zustand state not updating
```typescript
// State doesn't update in component
```

**Solutions:**
1. Check state mutation:
   ```typescript
   // Wrong - mutating state directly
   set((state) => {
     state.items.push(newItem);
     return state;
   });
   
   // Correct - return new state
   set((state) => ({
     ...state,
     items: [...state.items, newItem]
   }));
   ```

2. Verify store subscription:
   ```typescript
   // Ensure component subscribes to correct state slice
   const items = useStore((state) => state.items);
   ```

3. Check for stale closures:
   ```typescript
   // Use callback form to avoid stale state
   const updateItem = useCallback((id: string) => {
     setItems((current) => current.map(item => 
       item.id === id ? { ...item, updated: true } : item
     ));
   }, []);
   ```

## Database Issues

### PostgreSQL Issues

#### Issue: Connection pool exhausted
```bash
psycopg2.pool.PoolError: connection pool exhausted
```

**Solutions:**
1. Increase pool size:
   ```python
   # In database configuration
   SQLALCHEMY_ENGINE_OPTIONS = {
       "pool_size": 20,
       "max_overflow": 30,
       "pool_pre_ping": True,
       "pool_recycle": 3600
   }
   ```

2. Check for connection leaks:
   ```python
   # Always close sessions
   try:
       # Database operations
       pass
   finally:
       db.close()
   ```

3. Monitor active connections:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
   ```

#### Issue: Migration fails
```bash
alembic.util.exc.CommandError: Target database is not up to date
```

**Solutions:**
1. Check migration history:
   ```bash
   alembic history
   alembic current
   ```

2. Stamp database to specific revision:
   ```bash
   alembic stamp head
   ```

3. Generate new migration:
   ```bash
   alembic revision --autogenerate -m "description"
   ```

4. Manual migration fix:
   ```sql
   -- Check alembic_version table
   SELECT * FROM alembic_version;
   
   -- Update to correct version if needed
   UPDATE alembic_version SET version_num = 'correct_revision_id';
   ```

### Neo4j Issues

#### Issue: Connection timeout
```bash
neo4j.exceptions.ServiceUnavailable: Failed to establish connection
```

**Solutions:**
1. Check Neo4j service:
   ```bash
   docker-compose ps neo4j
   docker logs neo4j_container
   ```

2. Verify connection settings:
   ```python
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. Test connection:
   ```bash
   cypher-shell -a bolt://localhost:7687 -u neo4j -p password
   ```

4. Check memory settings:
   ```
   # neo4j.conf
   dbms.memory.heap.initial_size=512m
   dbms.memory.heap.max_size=1G
   ```

#### Issue: Cypher query performance
```cypher
Query takes too long to execute
```

**Solutions:**
1. Add appropriate indexes:
   ```cypher
   CREATE INDEX entity_type_index IF NOT EXISTS 
   FOR (e:Entity) ON (e.type);
   ```

2. Use PROFILE to analyze:
   ```cypher
   PROFILE MATCH (a:Account)-[:HOLDS]->(p:Position)
   WHERE a.balance > 1000000
   RETURN count(p);
   ```

3. Optimize query structure:
   ```cypher
   // Use LIMIT to reduce result set
   MATCH (a:Account)-[:HOLDS]->(p:Position)
   WHERE a.balance > 1000000
   RETURN a, p
   LIMIT 100;
   ```

### Redis Issues

#### Issue: Redis connection refused
```bash
redis.exceptions.ConnectionError: Connection refused
```

**Solutions:**
1. Check Redis service:
   ```bash
   docker-compose ps redis
   redis-cli ping
   ```

2. Verify Redis configuration:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

3. Check Redis logs:
   ```bash
   docker logs redis_container
   ```

4. Test connection:
   ```bash
   redis-cli -h localhost -p 6379
   ```

## Integration Issues

### MCP Server Issues

#### Issue: MCP server connection fails
```bash
Failed to connect to MCP server
```

**Solutions:**
1. Check server status:
   ```python
   # Test MCP server endpoint
   import requests
   response = requests.get("https://mcp-server.com/health")
   print(response.status_code)
   ```

2. Verify authentication:
   ```python
   # Check API key configuration
   headers = {"Authorization": f"Bearer {api_key}"}
   ```

3. Check network connectivity:
   ```bash
   curl -I https://mcp-server.com
   ping mcp-server.com
   ```

4. Review server logs:
   ```python
   # Enable debug logging
   logging.getLogger("mcp_service").setLevel(logging.DEBUG)
   ```

### WebSocket Issues

#### Issue: WebSocket connection drops
```javascript
WebSocket connection closed unexpectedly
```

**Solutions:**
1. Implement reconnection logic:
   ```javascript
   const connectWebSocket = () => {
     const ws = new WebSocket(url);
     
     ws.onclose = () => {
       setTimeout(connectWebSocket, 5000); // Reconnect after 5s
     };
     
     return ws;
   };
   ```

2. Add heartbeat mechanism:
   ```javascript
   setInterval(() => {
     if (ws.readyState === WebSocket.OPEN) {
       ws.send(JSON.stringify({ type: 'ping' }));
     }
   }, 30000);
   ```

3. Check server-side handling:
   ```python
   # Ensure proper WebSocket lifecycle management
   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       try:
           while True:
               data = await websocket.receive_text()
               # Process data
       except WebSocketDisconnect:
           # Clean up connection
           pass
   ```

## Performance Issues

### Backend Performance

#### Issue: Slow API responses
```bash
API endpoints taking > 5 seconds to respond
```

**Solutions:**
1. Add database query optimization:
   ```python
   # Use select_related for foreign keys
   query = session.query(Model).options(
       selectinload(Model.related_field)
   )
   ```

2. Implement caching:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_operation(param):
       # Cached operation
       pass
   ```

3. Use async operations:
   ```python
   async def async_endpoint():
       results = await asyncio.gather(
           async_operation_1(),
           async_operation_2()
       )
       return results
   ```

4. Profile slow queries:
   ```sql
   -- Enable query logging
   SET log_statement = 'all';
   SET log_min_duration_statement = 1000; -- Log queries > 1s
   ```

### Frontend Performance

#### Issue: Slow page loads
```bash
Page takes > 3 seconds to load
```

**Solutions:**
1. Implement code splitting:
   ```typescript
   const LazyComponent = lazy(() => import('./ExpensiveComponent'));
   
   function App() {
       return (
           <Suspense fallback={<Loading />}>
               <LazyComponent />
           </Suspense>
       );
   }
   ```

2. Optimize bundle size:
   ```bash
   npm run build -- --analyze
   ```

3. Use React.memo for expensive components:
   ```typescript
   const ExpensiveComponent = React.memo(({ data }) => {
       return <div>{/* Expensive rendering */}</div>;
   });
   ```

## Production Issues

### Deployment Issues

#### Issue: Docker container fails to start
```bash
Container exits with code 1
```

**Solutions:**
1. Check container logs:
   ```bash
   docker logs container_name
   ```

2. Debug container interactively:
   ```bash
   docker run -it --entrypoint /bin/bash image_name
   ```

3. Verify environment variables:
   ```bash
   docker exec container_name env
   ```

4. Check resource limits:
   ```bash
   docker stats container_name
   ```

#### Issue: Load balancer health checks fail
```bash
Health check endpoint returning 503
```

**Solutions:**
1. Verify health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check dependencies in health check:
   ```python
   @router.get("/health")
   async def health_check():
       # Test database connection
       try:
           db.execute("SELECT 1")
           return {"status": "healthy"}
       except Exception:
           raise HTTPException(status_code=503, detail="Database unavailable")
   ```

3. Review load balancer configuration:
   ```yaml
   # docker-compose.yml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

### Monitoring Issues

#### Issue: High memory usage
```bash
Container using > 90% memory
```

**Solutions:**
1. Profile memory usage:
   ```python
   import psutil
   import os
   
   process = psutil.Process(os.getpid())
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

2. Check for memory leaks:
   ```python
   # Use memory profiler
   from memory_profiler import profile
   
   @profile
   def function_to_profile():
       # Function code
       pass
   ```

3. Optimize database connections:
   ```python
   # Close connections properly
   try:
       # Database operations
       pass
   finally:
       session.close()
   ```

4. Implement garbage collection:
   ```python
   import gc
   gc.collect()  # Force garbage collection
   ```

## Monitoring and Debugging

### Logging Configuration

#### Structured Logging Setup
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_entry)

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Debug Tools

#### Backend Debugging
```python
# Add debug middleware
from fastapi import Request
import time

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"Request: {request.method} {request.url} - {process_time:.4f}s")
    return response
```

#### Frontend Debugging
```typescript
// Debug React renders
import { useEffect, useRef } from 'react';

const useWhyDidYouUpdate = (name: string, props: Record<string, any>) => {
  const previous = useRef<Record<string, any>>();
  
  useEffect(() => {
    if (previous.current) {
      const allKeys = Object.keys({ ...previous.current, ...props });
      const changedProps: Record<string, any> = {};
      
      allKeys.forEach(key => {
        if (previous.current![key] !== props[key]) {
          changedProps[key] = {
            from: previous.current![key],
            to: props[key]
          };
        }
      });
      
      if (Object.keys(changedProps).length) {
        console.log('[why-did-you-update]', name, changedProps);
      }
    }
    
    previous.current = props;
  });
};
```

### Performance Monitoring

#### Database Query Monitoring
```sql
-- Monitor slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Monitor connection usage
SELECT count(*) as connections, state
FROM pg_stat_activity
GROUP BY state;
```

#### Application Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Use in middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

This troubleshooting guide covers the most common issues you'll encounter when working with the Otomeshon platform. For issues not covered here, check the application logs and consider reaching out to the development team.
