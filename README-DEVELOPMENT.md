# Otomeshon Development Guide

## Quick Start Development Setup

For rapid development and testing, use the minimal setup that includes only essential services.

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Environment Setup

Copy environment templates:
```bash
# Backend environment
cp .env.example .env

# Frontend environment  
cp frontend/.env.example frontend/.env
```

Update the `.env` files with your preferred settings. The defaults work for local development.

### 2. Development Mode (Minimal Services)

For fast development with only essential services:

```bash
# Start minimal stack (PostgreSQL + Redis + Backend + Frontend)
docker-compose -f docker-compose.minimal.yml up -d

# View logs
docker-compose -f docker-compose.minimal.yml logs -f

# Stop services
docker-compose -f docker-compose.minimal.yml down
```

**Minimal stack includes:**
- PostgreSQL with pgvector (database)
- Redis (caching/sessions) 
- Backend API (simple mode)
- Frontend (development mode)

### 3. Full Development Mode

For development with all enterprise features:

```bash
# Start full stack (all services)
docker-compose -f docker-compose.dev.yml up -d

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Full stack includes:**
- PostgreSQL + pgvector
- Neo4j (knowledge graph)
- Redis (caching)
- Apache Kafka (event streaming)
- Temporal (workflow engine)
- Keycloak (authentication)
- Jaeger (observability)
- Prometheus + Grafana (monitoring)

### 4. Local Development (No Docker)

For pure local development without Docker:

#### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.simple.txt

# Run simple backend
python app/main_simple.py

# Or run full backend (requires services)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Application Modes

### Backend Modes

1. **Simple Mode** (`main_simple.py`):
   - Minimal dependencies
   - In-memory demo data
   - Simple JWT authentication
   - Perfect for local testing

2. **Full Mode** (`main.py`):
   - Complete enterprise stack
   - Real database integration
   - Keycloak authentication
   - All AI/ML features enabled

### Frontend Modes

1. **Development Mode** (`App.tsx`):
   - Basic routing and components
   - Minimal features for testing

2. **Banking Portal Mode** (`App.simple.tsx`):
   - Full custodian banking interface
   - Complete authentication flows
   - All banking modules enabled

## Service Access

When running the minimal stack:

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | admin@otomeshon.ai / admin123 |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | app / changeme |
| Redis | localhost:6379 | - |

When running the full stack, additional services:

| Service | URL | Credentials |
|---------|-----|-------------|
| Neo4j Browser | http://localhost:7474 | neo4j / changeme |
| Keycloak Admin | http://localhost:8080 | admin / admin |
| Jaeger UI | http://localhost:16686 | - |
| Grafana | http://localhost:3001 | admin / admin |

## Development Workflow

### 1. Feature Development
```bash
# Start minimal stack for fast iteration
docker-compose -f docker-compose.minimal.yml up -d

# Make code changes (volumes are mounted for hot reload)
# Backend: ./backend volume mounted to /app
# Frontend: ./frontend/src volume mounted to /app/src

# Test changes immediately (hot reload enabled)
```

### 2. Integration Testing
```bash
# Start full stack to test enterprise features
docker-compose -f docker-compose.dev.yml up -d

# Run integration tests
cd backend && python -m pytest tests/
cd frontend && npm test
```

### 3. Production Testing
```bash
# Use production-like configuration
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
```

**Database connection issues:**
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Connect to database directly
docker-compose exec db psql -U app -d otomeshon
```

**Frontend build issues:**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Backend import issues:**
```bash
# Ensure you're in the right directory
cd backend

# Check Python path
python -c "import sys; print(sys.path)"

# Install dependencies
pip install -r requirements.simple.txt
```

### Health Checks

All services include health checks. Check status:
```bash
# View service health
docker-compose ps

# Check specific service health
docker-compose exec backend curl http://localhost:8000/health
```

### Performance

**Minimal stack resource usage:**
- ~2GB RAM
- ~1GB disk
- 4 containers

**Full stack resource usage:**
- ~8GB RAM  
- ~5GB disk
- 10+ containers

## Next Steps

After successful setup:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Test Authentication**: Use the demo credentials
3. **Try Banking Features**: Navigate through the portal modules
4. **Check Logs**: Monitor application behavior
5. **Read Documentation**: Check the `docs/` directory for detailed guides

For production deployment, see `DEPLOYMENT.md`.